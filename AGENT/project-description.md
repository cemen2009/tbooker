# TBooker Project Description

This document describes the current repository state for architecture and
product-design discussions. It is context, not a plan or an assertion that
every represented domain feature already has an HTTP workflow.

## Project at a glance

TBooker is a Python restaurant table-booking API playground. Its domain models
and schemas cover cities, restaurants, tables, bookings, and users. The
application is built with FastAPI, Pydantic 2, SQLAlchemy 2's async ORM API,
PostgreSQL, and Alembic.

The project is still foundational: `src/main.py` exposes only `/health`. There
are repositories for the domain entities and one application service,
`UserService`; there are no CRUD routers or API endpoints for the domain yet.
The schemas describe intended request and response shapes, but should not be
mistaken for endpoints that already exist.

## Architecture and data flow

The intended separation is:

1. **Schemas** in `src/models/schemas/` validate request data and define
   response shapes.
2. **Services** coordinate use cases and translate persistence-layer errors
   into application/service errors. Currently this layer has only user
   operations.
3. **Repositories** use an injected SQLAlchemy `AsyncSession` for persistence.
   Most repositories offer CRUD operations that either commit or leave the
   transaction uncommitted. The user repository also has search, pagination,
   and email-duplicate translation.
4. **API boundary** translates service exceptions into HTTP responses. The
   handler is registered on the FastAPI application, but there are no domain
   routes using it yet.
5. **PostgreSQL** enforces relational and booking invariants that must hold
   across concurrent requests.

The exception package is split by layer:

- Repository errors are defined in `common/exceptions/repository.py`.
- Service errors are defined in `common/exceptions/service.py`.
- FastAPI exception-handler registration and service-error-to-HTTP mapping
  live in `common/exceptions/api.py`.

At present, user email conflicts are the implemented example of this flow:
PostgreSQL's `users_email_key` violation is translated to
`DuplicateEntityError`, then `UserService` translates that to
`UserAlreadyExistsError`, which the API handler maps to HTTP 409.
`UserNotFoundError` maps to HTTP 404. Other service errors are logged and
returned as HTTP 500 with a generic detail.

## Domain model and important invariants

- **City** stores a name, ISO alpha-2 country code, and IANA timezone. A city
  may have restaurants and users. City name plus country code is unique.
- **Restaurant** belongs to a city, has contact details, address, opening and
  closing times, optional description, and a pending/active/deactivated
  lifecycle. Restaurant names are unique within a city; email and phone are
  unique.
- **Table** belongs to a restaurant, has a restaurant-local number, capacity,
  and active/inactive status. Capacity must be positive; number is unique
  within a restaurant. Restaurant deletion cascades to its tables.
- **Booking** references a table and a user. It stores a date, start time, and
  number of half-hour slots. PostgreSQL generates a `tsrange` from those
  fields. A GiST exclusion constraint prevents overlapping ranges for the same
  table while allowing back-to-back bookings and simultaneous bookings on
  different tables.
- **User** stores normalized lowercase email, a write-only password property
  that validates and Argon2-hashes before persistence, name, admin/user role,
  invited/active/inactive status, optional city, and bookings. Email is
  unique, and a database check constraint enforces lowercase values.

`BaseModel` is the SQLAlchemy declarative base. Domain models define a default
ascending `order_by()` where applicable; timestamped entities share
`TimestampMixin`.

## Current user use case

`UserService` currently supports:

- Look up a user by ID or email, raising `UserNotFoundError` when absent.
- List users with search/status filters and pagination metadata. The
  repository searches email and names case-insensitively and escapes SQL LIKE
  wildcards. The service builds `/users?...` pagination paths, although that
  route does not currently exist.
- Create users with a hashed password and server-assigned `user` role and
  `active` status. Both a commit and a flush-without-commit variant exist.
- Update profile fields from `UserPut` or `UserPatch`, with duplicate-email
  checks and repository conflict translation.

The service does not currently implement delete, authentication, authorization,
password-change, or city/booking workflows. The schemas and status/role fields
exist, but do not alone imply those behaviors.

## Repository tree

```text
.
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── AGENT/
│   └── project-description.md
├── Dockerfile
├── README.md
├── alembic.ini
├── commands/
│   └── docker-entrypoint.sh
├── db_schema.png
├── docker-compose.yml
├── poetry.lock
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── common/
│   │   ├── __init__.py
│   │   └── exceptions/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       ├── repository.py
│   │       └── service.py
│   ├── core/
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── db/
│   │   │   ├── migrations/
│   │   │   │   ├── README
│   │   │   │   ├── env.py
│   │   │   │   ├── script.py.mako
│   │   │   │   └── versions/
│   │   │   │       └── 0703eff69588_initial_migration.py
│   │   │   └── sessions/
│   │   │       ├── __init__.py
│   │   │       └── postgres.py
│   │   ├── logging.py
│   │   └── security/
│   │       ├── __init__.py
│   │       ├── hashing.py
│   │       └── validation.py
│   ├── main.py
│   ├── models/
│   │   ├── orm/
│   │   │   ├── __init__.py
│   │   │   ├── base_model.py
│   │   │   ├── booking.py
│   │   │   ├── city.py
│   │   │   ├── restaurant.py
│   │   │   ├── table.py
│   │   │   └── user.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── booking.py
│   │       ├── city.py
│   │       ├── pagination.py
│   │       ├── restaurant.py
│   │       ├── table.py
│   │       └── user.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── booking.py
│   │   ├── city.py
│   │   ├── restaurant.py
│   │   ├── table.py
│   │   └── user.py
│   └── services/
│       └── user.py
└── tests/
    ├── conftest.py
    ├── repositories/
    │   ├── test_booking_repository.py
    │   ├── test_city_repository.py
    │   ├── test_restaurant_repository.py
    │   ├── test_table_repository.py
    │   └── test_user_repository.py
    ├── test_booking_constraints.py
    ├── test_credentials_validation.py
    ├── test_exception_handlers.py
    ├── test_model_ordering.py
    ├── test_restaurant_schema.py
    ├── test_settings.py
    └── test_user_service.py
```

## File guide

### Root and operations

- **`README.md`** — Project positioning, stack, architecture summary, setup,
  local run, and test commands.
- **`pyproject.toml`** — Poetry package/dependency definitions and Ruff, mypy,
  pytest, coverage, and Pyright configuration. Python target is 3.12.
- **`poetry.lock`** — Resolved Poetry dependency versions.
- **`requirements.txt`** — Pinned pip-style dependency list alongside the
  Poetry dependency files.
- **`.env.example`** — Example environment variables for app environment,
  debug mode, nested database settings (`DB__...`), and Redis settings. Do not
  treat its example credentials as production configuration.
- **`.gitignore`** — Excludes local IDE settings, virtual environments, Python
  caches, coverage output, and local `.env` files.
- **`Dockerfile`** — Multi-stage Python 3.12 image. Builds separate dev and
  prod dependency stages and app stages, copies `src/` into `/app`, and uses
  the entrypoint script. The final image stage is production.
- **`docker-compose.yml`** — Defines the app, PostgreSQL 18, and Redis 7
  services. The app expects a local `.env.dev` file; it waits for PostgreSQL
  health and Redis startup. PostgreSQL data is persisted in a named volume.
- **`commands/docker-entrypoint.sh`** — Starts Uvicorn on `0.0.0.0:8000`.
- **`alembic.ini`** — Points Alembic to `src/core/db/migrations`, prepends
  source paths, and leaves the database URL to be supplied by the environment
  module or caller.
- **`.github/workflows/ci.yml`** — GitHub Actions workflow for pushes, pull
  requests, and manual dispatch. Installs Poetry/Python 3.12 and runs
  `poetry run pytest`.
- **`db_schema.png`** — Static ER diagram. It appears older than the current ORM
  and migration (for example, some shown columns and booking fields differ);
  use the ORM and Alembic migration as the authoritative current schema.
- **`AGENT/project-description.md`** — This design-context document.

### Application entry point, common errors, and services

- **`src/main.py`** — Creates the FastAPI app, sets up logging, disposes the
  async PostgreSQL engine on shutdown, registers service exception handlers,
  and exposes `GET /health`. No domain routers are currently included.
- **`src/common/__init__.py`** — Empty package initializer.
- **`src/common/exceptions/__init__.py`** — Re-exports the common repository
  and service exception types.
- **`src/common/exceptions/repository.py`** — `RepositoryError` base class and
  `DuplicateEntityError`.
- **`src/common/exceptions/service.py`** — `ServiceError` base class plus
  `UserNotFoundError` and `UserAlreadyExistsError`.
- **`src/common/exceptions/api.py`** — Maps user-not-found to HTTP 404 and
  user-already-exists to HTTP 409; logs otherwise-unmapped service errors and
  returns HTTP 500. Exposes `register_exception_handlers(app)`.
- **`src/services/user.py`** — User use-case orchestration described above.
  Uses `UserRepository`, validates missing users and duplicate emails through
  service exceptions, hashes new passwords through the user model's setter,
  and builds the paginated user-list response.

### Core infrastructure

- **`src/core/config/settings.py`** — Pydantic settings models for database,
  Redis, and application environment/debug settings. Nested settings are
  configured with `__` as the environment-variable delimiter. Database URL is
  computed from its components.
- **`src/core/config/__init__.py`** — Cached `get_settings()` loader. Reads
  `ENVIRONMENT`, loads `.env.dev` or `.env.prod` when present, and constructs
  `Settings`.
- **`src/core/db/sessions/postgres.py`** — Builds the async SQLAlchemy engine
  and session factory, defines the PostgreSQL session dependency/context
  manager, and has a placeholder for non-dev SSL setup.
- **`src/core/db/sessions/__init__.py`** — Re-exports `get_postgres_db`.
- **`src/core/db/migrations/README`** — Alembic's short generic migration
  directory note.
- **`src/core/db/migrations/env.py`** — Alembic online/offline migration
  setup. Imports ORM models for metadata discovery and uses an explicitly
  supplied URL when present, otherwise the application database setting.
- **`src/core/db/migrations/script.py.mako`** — Template used by Alembic to
  generate migration files.
- **`src/core/db/migrations/versions/0703eff69588_initial_migration.py`** —
  Initial PostgreSQL schema migration for cities, restaurants, users, tables,
  and bookings. Enables `btree_gist`, defines a generated booking `tsrange`,
  and adds the no-overlap exclusion constraint.
- **`src/core/logging.py`** — Configures root logging level and a stderr
  formatter based on debug mode.
- **`src/core/security/__init__.py`** — Re-exports password hashing and
  credential validation helpers.
- **`src/core/security/hashing.py`** — Argon2 password hashing and verification
  via `pwdlib`.
- **`src/core/security/validation.py`** — Validates password length and
  character requirements, blocks common password patterns and simple
  leetspeak variants, and validates/normalizes email addresses.

### ORM models

- **`src/models/orm/__init__.py`** — Re-exports all ORM models and user
  enums; also used to ensure models are imported together.
- **`src/models/orm/base_model.py`** — SQLAlchemy declarative base with the
  `order_by()` contract and a created/updated timestamp mixin.
- **`src/models/orm/city.py`** — City columns, unique name/country constraint,
  restaurant/user relationships, and deterministic default ordering.
- **`src/models/orm/restaurant.py`** — Restaurant status enum, contact and
  opening-hour columns, unique constraints, city relationship, cascading
  restaurant-to-table relationship, and ordering.
- **`src/models/orm/table.py`** — Table status enum, number/capacity columns,
  positive-capacity check, per-restaurant number uniqueness, and restaurant
  and booking relationships.
- **`src/models/orm/booking.py`** — Booking date/time/slot fields, generated
  PostgreSQL range mapping, user/table relationships, and per-table overlap
  exclusion constraint declaration.
- **`src/models/orm/user.py`** — User roles/statuses, normalized lowercase
  email, hashed-password storage with write-only validating setter, optional
  city and booking relationships, and default ordering.

### Pydantic schemas

- **`src/models/schemas/__init__.py`** — Empty package initializer; schemas
  are imported from their modules directly.
- **`src/models/schemas/pagination.py`** — Generic `PageResponse[T]` with items,
  total, current page, page size, navigation paths, and computed total pages.
- **`src/models/schemas/city.py`** — City create/put/patch and list/detail
  schemas. Validates city names, country codes, and IANA timezones; PATCH
  requires at least one non-null field.
- **`src/models/schemas/restaurant.py`** — Restaurant create/put/patch and
  list/detail schemas, field constraints, city ID validation, and nested city
  name projection for list responses.
- **`src/models/schemas/table.py`** — Table create/put/patch and list/detail
  schemas, including capacity and identifier bounds.
- **`src/models/schemas/booking.py`** — Booking create/put/patch and
  list/detail schemas, including date/time, slot count, and positive ID
  validation.
- **`src/models/schemas/user.py`** — User create/put/patch and list/detail
  schemas. Applies email/password/name validation, disallows client-supplied
  role/status, disallows password changes through profile update schemas, and
  defines active/archive booking fields on the user detail shape.

### Repositories

- **`src/repositories/__init__.py`** — Re-exports repository classes.
- **`src/repositories/city.py`** — City CRUD methods; create/update/delete each
  have commit and no-commit variants.
- **`src/repositories/restaurant.py`** — Restaurant CRUD methods with
  commit and no-commit variants.
- **`src/repositories/table.py`** — Table CRUD methods with commit and
  no-commit variants.
- **`src/repositories/booking.py`** — Booking CRUD methods with commit and
  no-commit variants.
- **`src/repositories/user.py`** — User CRUD; case-normalized email lookup;
  filtered, escaped case-insensitive search and pagination; and translation
  of the named email uniqueness constraint to `DuplicateEntityError`. Its
  create/update methods roll back after an integrity error. Other constraint
  failures are re-raised as SQLAlchemy errors.

### Tests

- **`tests/conftest.py`** — Session-scoped PostgreSQL 18 Testcontainer and
  migrated async engine, per-test transaction/session fixture, and factories
  for tables and users. Docker must be available to run the database tests.
- **`tests/test_booking_constraints.py`** — Verifies overlapping bookings are
  rejected, adjacent bookings and different-table overlaps are allowed, and
  generated ranges have the expected duration.
- **`tests/test_credentials_validation.py`** — Tests password strength and
  common-password rejection, email normalization, schema integration, and
  international names.
- **`tests/test_exception_handlers.py`** — Verifies service errors are
  translated to HTTP 404, 409, or generic 500 responses.
- **`tests/test_model_ordering.py`** — Checks default model ordering columns
  and ascending sort direction.
- **`tests/test_restaurant_schema.py`** — Checks positive city ID validation
  for restaurant create and patch schemas.
- **`tests/test_settings.py`** — Tests environment-specific settings loading
  from temporary `.env.dev` and `.env.prod` files.
- **`tests/test_user_service.py`** — Tests user not-found and duplicate errors,
  password hashing and server-managed fields, profile patching, and
  pagination links.
- **`tests/repositories/test_booking_repository.py`** — Exercises booking
  repository CRUD and lookup behavior.
- **`tests/repositories/test_city_repository.py`** — Exercises city repository
  CRUD and lookup behavior.
- **`tests/repositories/test_restaurant_repository.py`** — Exercises
  restaurant repository CRUD and lookup behavior.
- **`tests/repositories/test_table_repository.py`** — Exercises table
  repository CRUD and lookup behavior.
- **`tests/repositories/test_user_repository.py`** — Covers user CRUD,
  commit/no-commit behavior, lowercase and unique email behavior, database
  enforcement of lowercase email, and paginated search/filter/order behavior.

## Configuration and local operation

Application configuration uses environment variables such as `ENVIRONMENT`,
`DEBUG`, `DB__HOST`, `DB__PORT`, `DB__USER`, `DB__PASSWORD`, `DB__NAME`, and
`REDIS__...`. The local configuration loader chooses `.env.dev` or `.env.prod`
based on `ENVIRONMENT`. `docker-compose.yml` references `.env.dev`, which is
ignored by Git; `.env.example` is a template and its settings need to match
the chosen local database setup.

Typical commands from the README:

```bash
poetry install
docker compose up -d postgres redis
poetry run uvicorn main:app --app-dir src --reload
poetry run pytest
```

The test suite provisions PostgreSQL using Testcontainers, so a working Docker
daemon is needed even though the app's local compose stack is a separate way to
run PostgreSQL and Redis.

## Design-relevant boundaries and current gaps

- There are no API routers, dependency-wired route handlers, authentication
  flows, or public/admin endpoint policies yet. `UserService` is not currently
  reachable through HTTP routes.
- Redis settings and a Redis dependency are present, but there is no Redis
  client or cache/rate-limit workflow in the current source tree.
- MinIO is a declared dependency and mentioned in the README as planned or
  available infrastructure, but there is no storage client or upload workflow
  in the source tree.
- The database schema is more developed than the HTTP/application layer:
  referential rules and booking concurrency protection are already encoded in
  PostgreSQL and tested.
- Current custom exception translation is implemented only for user email
  duplicates and the two user service errors. The other repositories currently
  expose database exceptions directly.
- `UserDetailResponse` describes active and archived bookings, but there is no
  service/query code shown here that assembles those lists.
- `db_schema.png` should be treated as a historical/design artifact rather
  than a reliable representation of the current Alembic schema.
