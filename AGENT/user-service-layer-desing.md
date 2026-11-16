# TBooker: User Service Design

*Draft v1. Scope: user, admin and superadmin accounts, authentication, lifecycle. Audience: project owner, future services (city, restaurant, table, booking), coding agents.*

## 1. Decision log

| # | Decision | Rationale / rejected alternatives |
| --- | --- | --- |
| 1 | Roles: `user`, `admin`, `superadmin`. One email = one account = one role. | No dual-role accounts; simpler auth and booking rules. |
| 2 | Single `users` table with a shared status enum; DB check constraints restrict which statuses each role may have. | One login path. Rejected: separate admin table. |
| 3 | Statuses: `pending`, `invited`, `unverified`, `active`, `deactivated` (`inactive` renamed). | `unverified` status chosen over an `email_verified_at` column and over a `pending_email` column. |
| 4 | Unverified users can log in but cannot book. Booking checks `status == active` against the DB, not token claims. | Verification takes effect immediately. |
| 5 | Admins have no password until invited. `pending` and `invited` admins cannot log in. | Ownership of the mailbox is proven by the invitation link. |
| 6 | Admin email is independent of restaurant email. | Coupling rejected (email changes would ripple into restaurants). |
| 7 | Restaurant to admin is M2M (`restaurant_admins`). Admins create restaurants as `pending`; superadmin activates them and adds co-admins. Admins ask for access to existing restaurants via `restaurant_access_request`. | Keeps ownership changes under platform control. |
| 8 | Auth lives in a separate `AuthService`. Short-lived JWT access token plus rotating refresh tokens in Redis. | Instant revocation on deactivation. Rejected: pure JWT (no revocation), Keycloak (custom flows would need constant sync). |
| 9 | One-time email links live in a DB table `user_tokens`, stored hashed. | Expiry must trigger state changes (`invited` to `deactivated`); a Redis TTL silently deletes instead. |
| 10 | Generic responses on registration, login, password reset, reactivation, admin request. | Prevents account enumeration. Rejected: 409 on duplicate email. |
| 11 | Deactivation is self-service and cascades. An admin is blocked while sole admin of any non-deactivated restaurant. | Avoids orphaned restaurants; no destructive cascade to restaurants. |
| 12 | Reactivation reuses the same user row via an emailed token (verify email + set new password). | Keeps history; prevents takeover with an old password. |
| 13 | Booking gets `status`: `active`, `cancelled`, `archived`. Exclusion constraint becomes partial on `active`. | Cancelled bookings free the table slot. |
| 14 | Celery Beat is the target for sweeps; MVP uses lazy fallbacks. | Beat is planned, not yet present. |
| 15 | Rate limiting is in scope, backed by Redis. | Redis already configured. |

## 2. Roles and state machines

### 2.1 Allowed statuses per role

| Role | Allowed statuses | Created by |
| --- | --- | --- |
| `user` | `unverified`, `active`, `deactivated` | Public registration |
| `admin` | `pending`, `invited`, `active`, `deactivated` | Public 'I own a restaurant' request |
| `superadmin` | `active` only (never deactivatable) | Seed or CLI only |

### 2.2 User lifecycle

| From | To | Trigger |
| --- | --- | --- |
| (none) | `unverified` | Registration |
| `unverified` | `active` | Email verification link used |
| `unverified`, `active` | `deactivated` | Self-deactivation (password confirmation required) |
| `deactivated` | `active` | Reactivation token used (verifies email and sets new password) |

### 2.3 Admin lifecycle

| From | To | Trigger |
| --- | --- | --- |
| (none) | `pending` | Public admin request (password is NULL) |
| `pending` | `invited` | Superadmin approves; invitation token issued; optional restaurant links created |
| `pending` | `deactivated` | Superadmin rejects (reason stored) |
| `invited` | `active` | Invitation link used; admin sets password |
| `invited` | `deactivated` | Invitation expired (Beat sweep, or lazily when the expired link is used) |
| `active` | `deactivated` | Self-deactivation, allowed only if not sole admin of any non-deactivated restaurant |
| `deactivated` | `pending` | Admin re-applies with the same email; row reused; stored password hash is cleared |

Superadmin can re-send an invitation while the admin is `invited`: the old token is invalidated, a new one issued, expiry extended.

## 3. Data model changes

### 3.1 `users`

- `UserRole`: add `superadmin`.
- `UserStatus`: rename `inactive` to `deactivated`; add `pending`, `unverified`. `invited` stays (admins only).
- New nullable text columns: `deactivation_reason` (informational only; no logic may branch on it) and `request_note` (free text from the admin request form, shown to superadmin).
- `hashed_password` becomes nullable.
- Check constraints:
  - `ck_users_role_status`: `(role='user' AND status IN ('unverified','active','deactivated')) OR (role='admin' AND status IN ('pending','invited','active','deactivated')) OR (role='superadmin' AND status='active')`
  - `ck_users_password_presence`: `hashed_password IS NOT NULL OR (role='admin' AND status IN ('pending','invited','deactivated'))`
  - `ck_users_deactivation_reason`: `deactivation_reason IS NULL OR status='deactivated'` (cleared on reactivation)
- Existing constraints stay: lowercase email check, unique email.
- Alembic: use `ALTER TYPE ... RENAME VALUE` and `ADD VALUE` inside `autocommit_block()`; new enum values cannot be used in the same transaction that adds them.

### 3.2 `user_tokens` (one-time email links, not session tokens)

| Column | Notes |
| --- | --- |
| `id` | PK |
| `user_id` | FK to `users`, cascade delete |
| `type` | enum: `email_verification`, `admin_invitation`, `password_reset`, `email_change`, `reactivation` |
| `token_hash` | SHA-256 of a `secrets.token_urlsafe(32)` value; unique. The raw value exists only in the email. |
| `new_email` | nullable; required exactly when `type='email_change'` (check constraint) |
| `expires_at`, `used_at`, `created_at` |  |

Partial unique index on `(user_id, type) WHERE used_at IS NULL`: issuing a new token invalidates the previous one of the same type (delete or mark used in the same transaction).

### 3.3 `restaurant_admins`

`restaurant_id`, `admin_id` (composite PK), `created_at`, `granted_by` (superadmin id). Service layer enforces that `admin_id` references a user with role `admin`. A restaurant must keep at least one admin unless it is `deactivated`.

### 3.4 `restaurant_access_request` (owned by the restaurant service; reserved here)

`id`, `admin_id`, `restaurant_id`, `status` (`pending`, `approved`, `rejected`), `message`, `resolved_by`, `resolved_at`, `created_at`. Partial unique index on `(admin_id, restaurant_id) WHERE status='pending'`. Approval inserts into `restaurant_admins`.

### 3.5 `bookings`

- New `status` enum: `active`, `cancelled`, `archived`.
- Drop and recreate the GiST exclusion constraint as partial: `WHERE status = 'active'`.
- `cancelled` = explicitly cancelled, including auto-cancel of future bookings on user deactivation (frees the slot). `archived` = finished bookings.

## 4. Flows

All mail is sent in the background (`BackgroundTasks` in MVP, Celery later) so response time never depends on the mail server.

### 4.1 Registration (user)

Always hash the submitted password (equalizes timing), then branch on the email:

| Email state | Action |
| --- | --- |
| New | Create `unverified` user; issue `email_verification` token; send verification mail |
| Existing `unverified` user | Re-issue verification token (cooldown applies) |
| Existing `active` user, or any admin | Send 'you already have an account' notice (login / reset links); no change |
| Existing `deactivated` user | Issue `reactivation` token; send reactivation mail |

Response is always `202` with the same body: 'if this email can be registered, check your inbox'.

### 4.2 Email verification

`POST` the token; valid and unexpired: `unverified` to `active`, token consumed. Resend: cooldown 60 s, max 5 per hour per account, new link invalidates the old one. Link TTL is a Pydantic setting.

### 4.3 Login, refresh, logout

- Login looks up by normalized email. Unknown email, wrong password, `deactivated`, `pending` and `invited` all return the same `401`; unknown emails verify against a dummy hash.
- Success for `unverified` and `active`: short-lived JWT access token (claims: `sub`, `role`, `iat`, `jti`; TTL setting, default 10 min) plus an opaque refresh token.
- Refresh tokens: stored hashed in Redis with `user_id`, `family_id`, expiry. Rotated on every use; reuse of a rotated token revokes the whole family.
- Revocation: on deactivation or password change, delete the user's refresh tokens and set `revoked_before:{user_id}` in Redis (TTL = access token TTL). The auth dependency rejects access tokens with `iat` earlier than that value (one Redis `GET` per request).
- Logout deletes the refresh token (and its family).

### 4.4 Admin onboarding

1. **Request** (public): `email`, `name`, `request_note`. New email creates a `pending` admin with no password. A `deactivated` admin goes back to `pending` with the password hash cleared. Any other existing account changes nothing. Response is always the generic `202`.
2. **Approve** (superadmin): lock the admin row, require `pending`, set `invited`, insert `restaurant_admins` for any restaurant ids supplied (may be empty; restaurants must exist and not be `deactivated`), issue an `admin_invitation` token (TTL setting, default 7 days), send mail.
3. **Reject** (superadmin): `pending` to `deactivated`, store `deactivation_reason`.
4. **Accept** (public, token): validate password rules, set password, `invited` to `active`, consume token. An expired token triggers the lazy transition `invited` to `deactivated` (reason `invitation expired`) and returns `410`.

Admin-created restaurants start `pending`; superadmin activates them. Requests to join existing restaurants go through `restaurant_access_request`.

### 4.5 Password reset and change

- Reset request: always generic `202`; a mail is sent only for `unverified` or `active` accounts. Confirm: set password, consume token, revoke all sessions.
- Change (authenticated): requires current password; revokes all other sessions.

### 4.6 Email change

1. Authenticated `POST` with `new_email` and `current_password`. Normalize the new email; reject if equal to the current one.
2. If the new email is already taken: still return `202`, send nothing (no enumeration). Otherwise issue an `email_change` token carrying `new_email`, mail it to the **new** address, and send a notice to the **old** one.
3. Confirm with the token: set `email = new_email` in one transaction, consume the token. A unique violation (race) returns `409`. Status does not change; the login email stays the old one until confirmation.

### 4.7 Deactivation

Endpoint requires password confirmation; superadmin is rejected with `403`. One transaction:

1. Lock the user row (`FOR UPDATE`).
2. **Admin:** lock rows of all restaurants linked via `restaurant_admins` (`FOR UPDATE`). If the admin is the only admin of any restaurant that is not `deactivated`, abort with `409` listing those restaurants. The lock prevents two co-admins from deactivating simultaneously and orphaning a restaurant.
3. **User:** for bookings with `status='active'`: future ones become `cancelled` (slot freed), past ones `archived`.
4. Set `status='deactivated'`, store optional `deactivation_reason`, delete unused tokens.
5. After commit: revoke sessions in Redis (4.3).

When the notification module exists, restaurants are notified of cancelled bookings. Cascades from restaurant deactivation to bookings belong to the restaurant service.

### 4.8 Reactivation

Registering with a deactivated email issues a `reactivation` token. Using it requires a new password (validated); the same row is reused (same id), `deactivation_reason` is cleared, status becomes `active`, old bookings stay `cancelled` or `archived`. Admins use the re-apply path in 4.4 instead.

## 5. API surface

| Method and path | Access | Notes |
| --- | --- | --- |
| `POST /auth/register` | public | Generic `202` (4.1) |
| `POST /auth/verify-email` | public | Token body; `204` |
| `POST /auth/verify-email/resend` | user, `unverified` | Rate limited |
| `POST /auth/login` | public | Returns access and refresh tokens |
| `POST /auth/refresh` | refresh token | Rotates |
| `POST /auth/logout` | authenticated | Revokes refresh token |
| `POST /auth/password-reset/request` | public | Generic `202` |
| `POST /auth/password-reset/confirm` | public | Token and new password |
| `POST /auth/reactivate/confirm` | public | Token and new password |
| `POST /auth/admin-requests` | public | Generic `202` |
| `POST /auth/admin-invitations/accept` | public | Token and password |
| `GET /users/me`, `PATCH /users/me`, `PUT /users/me` | authenticated | Profile; role, status and password stay server-managed |
| `POST /users/me/password` | authenticated | Current and new password |
| `POST /users/me/email-change`, `POST /users/me/email-change/confirm` | authenticated / token | See 4.6 |
| `POST /users/me/deactivate` | user, admin | Password confirmation |
| `GET /superadmin/admins?status=` | superadmin | List requests |
| `POST /superadmin/admins/{id}/approve` | superadmin | Body: `restaurant_ids` (optional) |
| `POST /superadmin/admins/{id}/reject` | superadmin | Body: reason |
| `POST /superadmin/admins/{id}/resend-invitation` | superadmin | `invited` only |
| `GET /users`, `GET /users/{id}` | superadmin | Existing list and detail with search and pagination |

## 6. Layering

- **Repositories** (SQL only, translate DB constraint errors): `UserRepository` (existing; add status transitions, lock-for-update, token-based lookups), `UserTokenRepository`, `RestaurantAdminRepository`, `BookingRepository` (bulk status update). Use the existing no-commit variants so a use case runs in one transaction.
- **Services** (use cases, raise service exceptions): `UserService` (profile, email change request, deactivation), `AuthService` (register, login, refresh, verify, reset, reactivate, accept invitation), `AdminOnboardingService` (request, approve, reject, resend).
- **Ports injected into services:** `Mailer` (fake in tests), `SessionStore` (Redis), `RateLimiter` (Redis), `Clock`.
- **API layer:** routers, auth dependencies (`get_current_principal`, `require_role(...)`, `require_active`), exception-to-HTTP mapping.

New service exceptions and HTTP mapping:

| Exception | HTTP |
| --- | --- |
| `InvalidCredentialsError` | 401 |
| `InvalidTokenError` | 400 |
| `TokenExpiredError` | 410 |
| `AccountNotActiveError` (booking while unverified) | 403 |
| `PermissionDeniedError` | 403 |
| `InvalidStateTransitionError` | 409 |
| `AdminOwnsRestaurantsError` | 409 |
| `RateLimitExceededError` | 429 (with `Retry-After`) |
| `UserAlreadyExistsError` (only email-change race, superadmin ops) | 409 |

## 7. Security

- Generic responses on register, login, reset, reactivation, admin request, email change to a taken address. Mail in the background plus equal hashing work to avoid timing leaks.
- Tokens: 256-bit random, SHA-256 stored, single use, TTLs in settings. Passwords: Argon2 and existing strength validation.
- No hard account lockout (denial-of-service vector); throttle per IP and per email, add CAPTCHA later if needed.
- Signing keys, TTLs and all limits below live in Pydantic settings.

| Endpoint group | Default limit |
| --- | --- |
| Login | 10 per 15 min per email+IP; 30 per 15 min per IP |
| Register | 5 per hour per IP |
| Verification resend | 60 s cooldown; 5 per hour per account |
| Password reset request | 3 per hour per email; 20 per hour per IP |
| Email change request | 5 per hour per account |
| Admin request | 3 per day per IP |
| Token confirm endpoints | 20 per hour per IP |

## 8. Async work

| Concern | MVP | With Celery Beat |
| --- | --- | --- |
| Sending mail | FastAPI `BackgroundTasks` | Celery task with retries |
| Booking `archived` | Derive in queries: `status='active' AND end < now()` | Periodic sweep persists `archived` |
| Invitation expiry | Lazy, on use; superadmin lists compute 'effectively expired' | Hourly sweep: `invited` to `deactivated` |
| Token cleanup | Not needed | Daily purge of used and expired tokens |
| Scheduled notifications | Out of scope | Reminders, news (separate design) |

## 9. Deferred and open items

- `request_note` on the admin form is an assumption; the exact public form fields are not final.
- Re-application after rejection or invitation expiry is allowed by the same path as other `deactivated` admins; confirm this is desired, and whether to cap attempts.
- `restaurant_access_request` and co-admin removal rules belong to the restaurant service design.
- Audit trail for superadmin actions (who approved or rejected) is deferred.
- Superadmin MFA, CAPTCHA, notification entity: deferred.

## 10. Implementation order and tests

1. Migrations: enums, columns, check constraints, `user_tokens`, `restaurant_admins`, booking `status` and partial exclusion constraint.
2. Settings (TTLs, limits, JWT keys), `Mailer`, token helper (generate, hash, consume).
3. `AuthService`: register, verify, login, refresh, logout, Redis session store.
4. `RateLimiter` and wiring on public endpoints.
5. Auth dependencies and routers; profile endpoints; password change; email change.
6. Deactivation and reactivation.
7. Admin onboarding and superadmin endpoints; superadmin seed CLI.

Test plan:

- Constraint tests (check constraints, partial exclusion allows re-booking a cancelled slot).
- Every state-machine transition, including every illegal one.
- Enumeration tests: identical body, status and comparable timing for known and unknown emails.
- Token tests: single use, expiry, invalidation on re-issue, lazy invitation expiry.
- Concurrency: two co-admins deactivating simultaneously; refresh token reuse detection.
- Deactivation cascade: future bookings cancelled, past archived, sessions revoked.
- Rate limit tests per endpoint group.
