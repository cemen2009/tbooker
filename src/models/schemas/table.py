from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from pydantic.json_schema import SkipJsonSchema

from models.orm.table import TableStatus
from models.schemas.pagination import PageResponse

TableNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)
]
TableCapacity = Annotated[int, Field(gt=0, le=32767)]
RestaurantId = Annotated[int, Field(gt=0)]


class TableBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: TableNumber
    capacity: TableCapacity
    restaurant_id: RestaurantId


class TableCreate(TableBase):
    """POST body; status defaults to active."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "number": "A1",
                    "capacity": 4,
                    "restaurant_id": 1,
                    "status": "active",
                }
            ]
        }
    )

    status: TableStatus = TableStatus.active


class TablePut(TableBase):
    """PUT body: full replacement, including status."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "number": "A1",
                    "status": "active",
                    "capacity": 6,
                    "restaurant_id": 1,
                }
            ]
        }
    )

    status: TableStatus


class TablePatch(BaseModel):
    """PATCH body: partial update; at least one non-null field is required."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"capacity": 6},
                {"number": "B2", "status": "inactive"},
            ]
        },
    )

    number: TableNumber | SkipJsonSchema[None] = None
    capacity: TableCapacity | SkipJsonSchema[None] = None
    restaurant_id: RestaurantId | SkipJsonSchema[None] = None
    status: TableStatus | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _require_non_empty_non_null(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("fields cannot be set to null")
        return self


class TableListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [{"id": 1, "number": "A1", "restaurant_id": 1}]},
    )

    id: int
    number: TableNumber
    restaurant_id: RestaurantId


class TableDetailResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "number": "A1",
                    "status": "active",
                    "capacity": 4,
                    "restaurant_id": 1,
                    "created_at": "2026-10-25T10:00:00Z",
                    "updated_at": "2026-10-25T10:00:00Z",
                }
            ]
        },
    )

    id: int
    number: TableNumber
    status: TableStatus
    capacity: TableCapacity
    restaurant_id: RestaurantId
    created_at: datetime
    updated_at: datetime


class TableListResponse(PageResponse[TableListItemResponse]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [{"id": 1, "number": "A1", "restaurant_id": 1}],
                    "total": 1,
                    "current_page": 1,
                    "per_page": 20,
                    "next_page": None,
                    "prev_page": None,
                    "first_page": "/tables?page=1&per_page=20",
                    "last_page": "/tables?page=1&per_page=20",
                    "total_pages": 1,
                }
            ]
        }
    )
