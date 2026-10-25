import pytest
from pydantic import ValidationError

from core.security import CredentialsValidator
from models.schemas.user import UserCreate, UserPatch, UserPut


@pytest.mark.parametrize(
    "password",
    [
        "StrongPass9!",
        "Spaces Are9!Allowed",
        "  StrongPass9!  ",
    ],
)
def test_validate_password_accepts_passwords_meeting_policy(password):
    assert CredentialsValidator.validate_password(password) == password


@pytest.mark.parametrize(
    "password",
    [
        "Ab1!xyz",
        "goodpass9!",
        "GoodPassword!",
        "GoodPassword9",
        "GOODPASS9!",
        "Password123!",
        "GoodPass9 ",
        "GoodPass9\x00",
        "  ",
        "A" * 129,
    ],
)
def test_validate_password_rejects_passwords_outside_policy(password):
    with pytest.raises(ValueError):
        CredentialsValidator.validate_password(password)


def test_validate_password_reports_all_strength_failures():
    with pytest.raises(ValueError) as error:
        CredentialsValidator.validate_password("")

    message = str(error.value)
    assert "at least 8 characters" in message
    assert "uppercase letter" in message
    assert "lowercase letter" in message
    assert "digit" in message
    assert "special character" in message


def test_validate_password_rejects_non_string_values():
    with pytest.raises(ValueError, match="must be a string"):
        CredentialsValidator.validate_password(None)


def test_validate_email_normalizes_and_rejects_invalid_addresses():
    assert CredentialsValidator.validate_email("Alex@EXAMPLE.COM") == "alex@example.com"

    with pytest.raises(ValueError):
        CredentialsValidator.validate_email("not-an-email")


@pytest.mark.parametrize(
    "password",
    [
        "QwErTy9!",
        "My-QWERTY-9!",
        "P@ssword9!",
        "P@$$w0rd2026!",
        "MyPassword9!",
        "1Qaz2Wsx!",
        "Xx-1qaz-2wsx-9!",
    ],
)
def test_validate_password_rejects_common_password_variations(password):
    with pytest.raises(ValueError, match="common password"):
        CredentialsValidator.validate_password(password)


def test_user_create_uses_password_policy():
    user_data = {
        "email": "alex@example.com",
        "password": "weakpass",
        "first_name": "Alex",
        "last_name": "Smith",
    }

    with pytest.raises(ValidationError):
        UserCreate.model_validate(user_data)

    user_data["password"] = "TbookerExample9!"
    assert UserCreate.model_validate(user_data).password == "TbookerExample9!"


def test_user_put_and_patch_do_not_accept_password_changes():
    user_fields = {
        "email": "alex@example.com",
        "first_name": "Alex",
        "last_name": "Smith",
        "city_id": None,
    }

    assert UserPut.model_validate(user_fields)
    with pytest.raises(ValidationError):
        UserPut.model_validate({**user_fields, "password": "TbookerExample9!"})

    assert UserPatch.model_validate({"first_name": "Alexandra"})
    with pytest.raises(ValidationError):
        UserPatch.model_validate({"password": "TbookerExample9!"})

    assert "password" not in UserPut.model_fields
    assert "password" not in UserPatch.model_fields
