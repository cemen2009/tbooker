from datetime import datetime, time
from typing import Annotated, Self

from pydantic import (
    AliasPath,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from models.orm.restaurant import RestaurantStatus
from models.schemas.pagination import PageResponse

RestaurantEmail = Annotated[EmailStr, Field(max_length=255)]
RestaurantPhone = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)
]
RestaurantName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=125)
]
RestaurantDescription = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=625)
]
RestaurantAddress = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]
CityId = Annotated[int, Field(...)]


class RestaurantBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: RestaurantEmail
    phone: RestaurantPhone
    name: RestaurantName
    description: RestaurantDescription | None
    opens_at: time
    closes_at: time
    address: RestaurantAddress
    city_id: int


class RestaurantCreate(RestaurantBase):
    """POST body; status defaults to pending and is server-managed."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "hello@example.com",
                    "phone": "+380441234567",
                    "name": "Lviv Bistro",
                    "description": "Modern Ukrainian cuisine",
                    "opens_at": "09:00:00",
                    "closes_at": "22:00:00",
                    "address": "1 Rynok Square",
                    "city_id": 1,
                }
            ]
        }
    )


class RestaurantPut(RestaurantBase):
    """PUT body: full replacement, every client-managed field is required."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "hello@example.com",
                    "phone": "+380441234567",
                    "name": "Lviv Bistro",
                    "description": "Updated menu and dining room",
                    "opens_at": "10:00:00",
                    "closes_at": "23:00:00",
                    "address": "2 Rynok Square",
                    "city_id": 1,
                }
            ]
        }
    )


class RestaurantPatch(BaseModel):
    """PATCH body: partial update, at least one field; fields cannot be null."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"description": "Seasonal Ukrainian cuisine"},
                {"opens_at": "10:00:00", "closes_at": "23:00:00"},
            ]
        },
    )

    email: RestaurantEmail | SkipJsonSchema[None] = None
    phone: RestaurantPhone | SkipJsonSchema[None] = None
    name: RestaurantName | SkipJsonSchema[None] = None
    description: RestaurantDescription | None = None
    opens_at: time | SkipJsonSchema[None] = None
    closes_at: time | SkipJsonSchema[None] = None
    address: RestaurantAddress | SkipJsonSchema[None] = None
    city_id: CityId | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _require_non_empty_non_null(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(
            getattr(self, field) is None and field != "description"
            for field in self.model_fields_set
        ):
            raise ValueError("fields cannot be set to null")
        return self


class RestaurantListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "email": "hello@example.com",
                    "phone": "+380441234567",
                    "name": "Lviv Bistro",
                    "description": "Modern Ukrainian cuisine",
                    "city": "Lviv",
                    "address": "1 Rynok Square",
                }
            ]
        },
    )

    email: RestaurantEmail
    phone: RestaurantPhone
    name: RestaurantName
    description: RestaurantDescription | None
    city: str = Field(validation_alias=AliasPath("city", "name"))
    address: RestaurantAddress


class RestaurantDetailResponse(RestaurantBase):
    """Single-restaurant payload; can grow without changing the list payload."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "email": "hello@example.com",
                    "phone": "+380441234567",
                    "name": "Lviv Bistro",
                    "description": "Modern Ukrainian cuisine",
                    "opens_at": "09:00:00",
                    "closes_at": "22:00:00",
                    "status": "active",
                    "address": "1 Rynok Square",
                    "city_id": 1,
                    "created_at": "2026-10-20T12:00:00Z",
                    "updated_at": "2026-10-20T12:00:00Z",
                }
            ]
        },
    )

    id: int
    status: RestaurantStatus
    created_at: datetime
    updated_at: datetime


class RestaurantListResponse(PageResponse[RestaurantListItemResponse]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "email": "hello@example.com",
                            "phone": "+380441234567",
                            "name": "Lviv Bistro",
                            "description": "Modern Ukrainian cuisine",
                            "city": "Lviv",
                            "address": "1 Rynok Square",
                        }
                    ],
                    "total": 1,
                    "current_page": 1,
                    "per_page": 20,
                    "next_page": None,
                    "prev_page": None,
                    "first_page": "/restaurants?page=1&per_page=20",
                    "last_page": "/restaurants?page=1&per_page=20",
                    "total_pages": 1,
                }
            ]
        }
    )
