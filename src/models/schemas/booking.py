from datetime import date, datetime, time
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema

from models.schemas.pagination import PageResponse

SlotCount = Annotated[int, Field(gt=0, le=32767)]
TableId = Annotated[int, Field(gt=0)]
UserId = Annotated[int, Field(gt=0)]


class BookingBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    booking_date: date
    start_time: time
    slot_count: SlotCount
    table_id: TableId
    user_id: UserId


class BookingCreate(BookingBase):
    """POST body; the generated time range and timestamps are server-managed."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "booking_date": "2026-10-25",
                    "start_time": "18:00:00",
                    "slot_count": 2,
                    "table_id": 1,
                    "user_id": 2,
                }
            ]
        }
    )


class BookingPut(BookingBase):
    """PUT body: full replacement of booking fields."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "booking_date": "2026-10-25",
                    "start_time": "19:00:00",
                    "slot_count": 3,
                    "table_id": 1,
                    "user_id": 2,
                }
            ]
        }
    )


class BookingPatch(BaseModel):
    """PATCH body: partial update; at least one non-null field is required."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"start_time": "19:00:00"},
                {"booking_date": "2026-10-26", "slot_count": 3},
            ]
        },
    )

    booking_date: date | SkipJsonSchema[None] = None
    start_time: time | SkipJsonSchema[None] = None
    slot_count: SlotCount | SkipJsonSchema[None] = None
    table_id: TableId | SkipJsonSchema[None] = None
    user_id: UserId | SkipJsonSchema[None] = None

    @model_validator(mode="after")
    def _require_non_empty_non_null(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("fields cannot be set to null")
        return self


class BookingListItemResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "booking_date": "2026-10-25",
                    "start_time": "18:00:00",
                    "slot_count": 2,
                    "table_id": 1,
                }
            ]
        },
    )

    id: int
    booking_date: date
    start_time: time
    slot_count: SlotCount
    table_id: TableId


class BookingDetailResponse(BookingListItemResponse):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "booking_date": "2026-10-25",
                    "start_time": "18:00:00",
                    "slot_count": 2,
                    "table_id": 1,
                    "user_id": 2,
                    "created_at": "2026-10-25T10:00:00Z",
                    "updated_at": "2026-10-25T10:00:00Z",
                }
            ]
        },
    )

    user_id: UserId
    created_at: datetime
    updated_at: datetime


class BookingListResponse(PageResponse[BookingListItemResponse]):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {
                            "id": 1,
                            "booking_date": "2026-10-25",
                            "start_time": "18:00:00",
                            "slot_count": 2,
                            "table_id": 1,
                        }
                    ],
                    "total": 1,
                    "current_page": 1,
                    "per_page": 20,
                    "next_page": None,
                    "prev_page": None,
                    "first_page": "/bookings?page=1&per_page=20",
                    "last_page": "/bookings?page=1&per_page=20",
                    "total_pages": 1,
                }
            ]
        }
    )
