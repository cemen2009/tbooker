from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from core.security import CredentialsValidator
from models.orm.user import UserRole, UserStatus
from models.schemas.booking import BookingListItemResponse
from models.schemas.pagination import PageResponse

UserEmail = Annotated[
    str,
    Field(max_length=255, json_schema_extra={"format": "email"}),
    BeforeValidator(CredentialsValidator.validate_email),
]
UserPassword = Annotated[
    str,
    StringConstraints(min_length=8, max_length=128),
    Field(
        description=(
            "8-128 characters; must contain uppercase and lowercase letters, "
            "a digit, and one of @$!%*?&#, and must not be a common password "
            "or variation."
        )
    ),
    BeforeValidator(CredentialsValidator.validate_password),
]
UserFirstName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=75)
]
UserLastName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=90)
]
CityId = Annotated[int, Field(gt=0)]


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: UserEmail
    password: UserPassword
    first_name: UserFirstName
    last_name: UserLastName


class UserCreate(UserBase):
    """POST body; role and status are managed by the server."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "alex@example.com",
                    "password": "TbookerExample9!",
                    "first_name": "Alex",
                    "last_name": "Smith",
                    "city_id": 1,
                }
            ]
        }
    )

    city_id: CityId | None = None


class UserPut(BaseModel):
    """PUT body: full replacement of profile fields; password changes are separate."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "email": "alex@example.com",
                    "first_name": "Alex",
                    "last_name": "Smith",
                    "city_id": None,
                }
            ]
        },
    )

    email: UserEmail
    first_name: UserFirstName
    last_name: UserLastName
    city_id: CityId | None


class UserPatch(BaseModel):
    """PATCH body: partial update; city_id may be cleared with null."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"first_name": "Alexandra"},
                {"city_id": None},
            ]
        },
    )

    email: UserEmail | SkipJsonSchema[None] = None
    first_name: UserFirstName | SkipJsonSchema[None] = None
    last_name: UserLastName | SkipJsonSchema[None] = None
    city_id: CityId | None = None

    @model_validator(mode="after")
    def _require_non_empty_non_null(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(
            getattr(self, field) is None and field != "city_id"
            for field in self.model_fields_set
        ):
            raise ValueError("fields cannot be set to null")
        return self


class UserListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "alex@example.com",
                    "role": "user",
                    "status": "active",
                }
            ]
        },
    )

    id: int
    email: UserEmail
    role: UserRole
    status: UserStatus


class UserDetailResponse(UserListItemResponse):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "alex@example.com",
                    "role": "user",
                    "status": "active",
                    "first_name": "Alex",
                    "last_name": "Smith",
                    "city_id": None,
                    "active_bookings": [
                        {
                            "id": 2,
                            "booking_date": "2026-11-02",
                            "start_time": "18:00:00",
                            "slot_count": 2,
                            "table_id": 4,
                        }
                    ],
                    "archive_bookings": [
                        {
                            "id": 1,
                            "booking_date": "2026-10-25",
                            "start_time": "19:00:00",
                            "slot_count": 3,
                            "table_id": 2,
                        }
                    ],
                    "created_at": "2026-10-25T10:00:00Z",
                    "updated_at": "2026-10-25T10:00:00Z",
                }
            ]
        },
    )

    first_name: UserFirstName
    last_name: UserLastName
    city_id: CityId | None
    active_bookings: list[BookingListItemResponse]
    archive_bookings: list[BookingListItemResponse]
    created_at: datetime
    updated_at: datetime


class UserListResponse(PageResponse[UserListItemResponse]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": 1,
                            "email": "alex@example.com",
                            "role": "user",
                            "status": "active",
                        }
                    ],
                    "total": 1,
                    "current_page": 1,
                    "per_page": 20,
                    "next_page": None,
                    "prev_page": None,
                    "first_page": "/users?page=1&per_page=20",
                    "last_page": "/users?page=1&per_page=20",
                    "total_pages": 1,
                }
            ]
        }
    )
