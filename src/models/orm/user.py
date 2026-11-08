from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SaEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from models.db.base_model import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from models.db.booking import BookingModel
    from models.db.city import CityModel


class UserRole(Enum):
    admin = "admin"
    user = "user"


class UserStatus(Enum):
    invited = "invited"
    active = "active"
    inactive = "inactive"


class UserModel(BaseModel, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
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

    @validates("email")
    def normalize_email(self, _key: str, email: str) -> str:
        return email.lower()

    def __repr__(self) -> str:
        return f"UserModel(id={self.id!r}, email={self.email!r}, first_name={self.first_name!r}, last_name={self.last_name!r})"

    @classmethod
    def order_by(cls) -> list:
        return [cls.first_name, cls.last_name, cls.email, cls.id]
