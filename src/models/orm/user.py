from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Enum as SaEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.elements import ColumnElement

from models.orm.base_model import BaseModel, TimestampMixin
from core.security import CredentialsValidator, Hasher

if TYPE_CHECKING:
    from models.orm.booking import BookingModel
    from models.orm.city import CityModel


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
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password", String(255), nullable=False
    )
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

    @classmethod
    def order_by(cls) -> list[ColumnElement[Any]]:
        return [cls.last_name.asc(), cls.first_name.asc(), cls.id.asc()]

    @property
    def password(self) -> None:
        raise AttributeError(
            "Password is write-only. Use the setter to set the password."
        )

    @password.setter
    def password(self, raw_password: str) -> None:
        """
        Set the user's password after validating its strength and hashing it.
        """
        CredentialsValidator.validate_password(raw_password)
        self._hashed_password = Hasher.hash_password(raw_password)
