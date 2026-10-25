from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SaEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import ColumnElement

from models.db.base_model import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from models.db.booking import BookingModel
    from models.db.restaurant import RestaurantModel


class TableStatus(Enum):
    active = "active"
    inactive = "inactive"


class TableModel(BaseModel, TimestampMixin):
    __tablename__ = "tables"
    __table_args__ = (
        CheckConstraint("capacity > 0", name="ck_table_capacity_is_positive"),
        UniqueConstraint("restaurant_id", "number", name="uq_table_restaurant_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    number: Mapped[str] = mapped_column(String(32))
    status: Mapped[TableStatus] = mapped_column(
        SaEnum(TableStatus), default=TableStatus.active
    )
    capacity: Mapped[int] = mapped_column(SmallInteger)

    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE")
    )
    restaurant: Mapped["RestaurantModel"] = relationship(
        "RestaurantModel", back_populates="tables"
    )

    bookings: Mapped[list["BookingModel"]] = relationship(
        "BookingModel", back_populates="table"
    )

    @classmethod
    def order_by(cls) -> list[ColumnElement[Any]]:
        return [cls.number.asc(), cls.id.asc()]

    def __repr__(self) -> str:
        return f"Table(id={self.id!r}, number={self.number!r})"
