import re

import email_validator

_COMMON_PASSWORD_PATTERNS = frozenset({"qwerty", "password", "1qaz2wsx"})
_LEETSPEAK_TRANSLATION = str.maketrans(
    {
        "@": "a",
        "4": "a",
        "$": "s",
        "5": "s",
        "0": "o",
        "3": "e",
        "7": "t",
    }
)


def _normalize_password_for_blocklist(password: str) -> str:
    normalized_password = password.casefold().translate(_LEETSPEAK_TRANSLATION)
    return "".join(
        character for character in normalized_password if character.isalnum()
    )


class CredentialsValidator:
    @staticmethod
    def validate_password(password: object) -> str:
        """Validate password strength and reject common-password variations."""
        if not isinstance(password, str):
            raise ValueError("Password must be a string.")

        errors = []
        if len(password) < 8:
            errors.append("be at least 8 characters long")
        if len(password) > 128:
            errors.append("be no more than 128 characters long")
        if not re.search(r"[A-Z]", password):
            errors.append("contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            errors.append("contain at least one lowercase letter")
        if not re.search(r"\d", password):
            errors.append("contain at least one digit")
        if not re.search(r"[@$!%*?&#]", password):
            errors.append(
                "contain at least one special character: @, $, !, %, *, ?, #, &"
            )
        normalized_password = _normalize_password_for_blocklist(password)
        if any(
            pattern in normalized_password for pattern in _COMMON_PASSWORD_PATTERNS
        ):
            errors.append(
                "not be a common password or a variation of one "
                "(qwerty, password, or 1qaz2wsx)"
            )

        if errors:
            raise ValueError("Password must " + ", ".join(errors) + ".")
        return password

    @staticmethod
    def validate_email(email: object) -> str:
        """Validate an email address and return its normalized form."""
        if not isinstance(email, str):
            raise ValueError("Email must be a string.")
        if len(email) > 255:
            raise ValueError("Email must be at most 255 characters long.")
        try:
            email_info = email_validator.validate_email(
                email, check_deliverability=False
            )
        except email_validator.EmailNotValidError as error:
            raise ValueError(str(error)) from error

        return email_info.normalized.lower()
