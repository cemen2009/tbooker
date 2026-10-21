import zoneinfo
from typing import Annotated, Self

import pycountry
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    StringConstraints,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from models.schemas.pagination import PageResponse


_VALID_TIMEZONES: frozenset[str] = frozenset(zoneinfo.available_timezones())


def _normalize_country_code(value: object) -> object:
    return value.strip().upper() if isinstance(value, str) else value


def _validate_timezone(value: str) -> str:
    if value not in _VALID_TIMEZONES:
        raise ValueError(f"'{value}' is not a valid IANA timezone identifier")
    return value


def _validate_country_code(value: str) -> str:
    if pycountry.countries.get(alpha_2=value) is None:
        raise ValueError(f"'{value}' is not a valid ISO 3166-1 alpha-2 country code")
    return value


CityName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
CountryCode = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z]{2}$"),
    BeforeValidator(_normalize_country_code),
    AfterValidator(_validate_country_code),
]
Timezone = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
    AfterValidator(_validate_timezone),
]


class CityBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: CityName
    country_code: CountryCode
    timezone: Timezone


class CityCreate(CityBase):
    """POST body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Lviv", "country_code": "UA", "timezone": "Europe/Kyiv"}
            ]
        },
    )


class CityPut(CityBase):
    """PUT body: full replacement, every field required."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Kraków",
                    "country_code": "PL",
                    "timezone": "Europe/Warsaw",
                }
            ]
        },
    )


class CityPatch(BaseModel):
    """PATCH body: partial update, at least one field; fields cannot be null."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"timezone": "Europe/Kyiv"},
                {"name": "Kharkiv", "country_code": "UA"},
            ]
        },
    )

    name: CityName | SkipJsonSchema[None] = None
    country_code: CountryCode | SkipJsonSchema[None] = None
    timezone: Timezone | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _require_non_empty_non_null(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("fields cannot be set to null")
        return self


class CityListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Kyiv",
                    "country_code": "UA",
                },
                {
                    "name": "Warsaw",
                    "country_code": "PL",
                },
            ]
        },
    )

    name: CityName
    country_code: CountryCode


class CityDetailResponse(CityBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Kyiv",
                    "country_code": "UA",
                    "timezone": "Europe/Kyiv",
                }
            ]
        },
    )

    id: int


class CityListResponse(PageResponse[CityListItemResponse]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "name": "Kyiv",
                            "country_code": "UA",
                        },
                        {
                            "name": "Warsaw",
                            "country_code": "PL",
                        },
                    ],
                    "total": 42,
                    "current_page": 1,
                    "per_page": 20,
                    "next_page": "/cities?page=2&per_page=20",
                    "prev_page": None,
                    "first_page": "/cities?page=1&per_page=20",
                    "last_page": "/cities?page=3&per_page=20",
                    "total_pages": 3,
                }
            ]
        }
    )
