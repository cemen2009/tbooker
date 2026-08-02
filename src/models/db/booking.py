from typing import TYPE_CHECKING
from datetime import date, time

from sqlalchemy import ForeignKey, Time, Date, SmallInteger, column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSRANGE, ExcludeConstraint

from models.db.base_model import BaseModel, TimestampMixin


if TYPE_CHECKING:
    from models.db.table import TableModel
    from models.db.user import UserModel


class BookingModel(BaseModel, TimestampMixin):
    __tablename__ = "bookings"
    __table_args__ = (
        ExcludeConstraint(
            (column("table_id"), "="),
            (column("time_range"), "&&"),  # && = overlap
            name="ex_booking_no_overlap_per_table",
        ),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # generated column. see in initial Alembic migration
    time_range: Mapped[str] = mapped_column(TSRANGE, system=True)
    
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id", ondelete="RESTRICT"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    table: Mapped["TableModel"] = relationship("TableModel", back_populates="bookings")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="bookings")

    def __repr__(self) -> str:
        return f"BookingModel(id={self.id!r})"
