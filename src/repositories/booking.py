from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orm.booking import BookingModel


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_booking_and_dont_commit(
        self, booking: BookingModel
    ) -> BookingModel:
        self.session.add(booking)
        await self.session.flush()
        return booking

    async def create_new_booking(self, booking: BookingModel) -> BookingModel:
        await self.create_new_booking_and_dont_commit(booking)
        await self.session.commit()
        return booking

    async def get_booking_by_id(self, booking_id: int) -> BookingModel | None:
        statement = select(BookingModel).where(BookingModel.id == booking_id)
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def update_booking(self, booking: BookingModel) -> BookingModel:
        await self.session.flush()
        return booking

    async def delete_booking(self, booking: BookingModel) -> None:
        await self.session.delete(booking)
        await self.session.flush()
