from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Enum as SaEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base_model import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from models.db.city import CityModel
    from models.db.booking import BookingModel


class UserRole(Enum):
    admin = "admin"
    user = "user"


class UserStatus(Enum):
    invited = "invited"
    active = "active"
    inactive = "inactive"


class UserModel(BaseModel, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(name="password")
    first_name: Mapped[str] = mapped_column(String(75))
    last_name: Mapped[str] = mapped_column(String(90))
    role: Mapped[UserRole] = mapped_column(SaEnum(UserRole))
    status: Mapped[UserStatus] = mapped_column(SaEnum(UserStatus))

    city_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cities.id"))
    city: Mapped[Optional["CityModel"]] = relationship(
        "CityModel", back_populates="users"
    )

    bookings: Mapped[list["BookingModel"]] = relationship(
        "BookingModel", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"UserModel(id={self.id!r}, email={self.email!r}, first_name={self.first_name!r}, last_name={self.last_name!r})"
