from typing import TYPE_CHECKING
from datetime import time
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Time, Enum, UniqueConstraint, Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base_model import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from models.db.city import CityModel
    from models.db.table import TableModel


class RestaurantStatus(StrEnum):
    pending = "pending"
    active = "active"
    deactivated = "deactivated"


class RestaurantModel(TimestampMixin, BaseModel):
    __tablename__ = "restaurants"
    __table_args__ = (
        UniqueConstraint("name", "city_id", name="uq_restaurant_name_city_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(125))
    description: Mapped[str] = mapped_column(String(625))

    # opens_at=09:00 means "9am in whatever timezone self.city.timezone says"
    opens_at: Mapped[time] = mapped_column(Time(timezone=False))
    closes_at: Mapped[time] = mapped_column(Time(timezone=False))

    status: Mapped[RestaurantStatus] = mapped_column(
        SaEnum(RestaurantStatus), default=RestaurantStatus.pending
    )
    address: Mapped[str] = mapped_column(String(255))

    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id", ondelete="RESTRICT"))
    city: Mapped["CityModel"] = relationship("CityModel", back_populates="restaurants")

    tables: Mapped[list["TableModel"]] = relationship(
        "TableModel", back_populates="restaurant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"RestaurantModel(id={self.id!r}, name={self.name!r}, email={self.email!r})"
        )
