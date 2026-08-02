from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.db.base_model import BaseModel

if TYPE_CHECKING:
    from models.db.restaurant import RestaurantModel


class CityModel(BaseModel):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country_code: Mapped[str] = mapped_column(
        String(2), comment="ISO 3166-1 alpha-2 country code, e.g. 'UA', 'US'"
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        comment=(
            "IANA timezone identifier, e.g. 'Europe/Kyiv'. "
            "Do not use fixed UTC offsets — they break under DST/political "
            "timezone shifts (e.g. Ukraine UTC+2/+3)."
        ),
    )

    restaurants: Mapped[list["RestaurantModel"]] = relationship(
        "RestaurantModel", back_populates="city"
    )

    def __repr__(self) -> str:
        return f"CityModel(id={self.id!r}, name={self.name!r})"
