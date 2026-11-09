from datetime import date, time

from models.orm.booking import BookingModel
from repositories import BookingRepository


async def test_booking_repository_crud(db_session, table_factory, user_factory):
    table = await table_factory()
    user = await user_factory()
    repository = BookingRepository(db_session)
    booking = BookingModel(
        booking_date=date(2026, 11, 8),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )

    created = await repository.create_new_booking(booking)
    assert created.id is not None
    assert await repository.get_booking_by_id(created.id) is created
    assert await repository.get_booking_by_id(-1) is None

    created.start_time = time(19, 0)
    assert await repository.update_booking(created) is created
    await repository.delete_booking(created)
    assert await repository.get_booking_by_id(created.id) is None
