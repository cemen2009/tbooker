from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from models.db.booking import BookingModel


async def test_overlapping_booking_on_same_table_rejected(
    db_session, table_factory, user_factory
):
    table = await table_factory()
    user = await user_factory()

    first_booking = BookingModel(
        booking_date=date(2026, 8, 2),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )

    db_session.add(first_booking)
    await db_session.commit()

    overlapping_booking = BookingModel(
        booking_date=date(2026, 8, 2),
        start_time=time(18, 30),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )
    db_session.add(overlapping_booking)

    with pytest.raises(IntegrityError):
        await db_session.commit()


async def test_back_to_back_bookings_on_same_table_are_allowed(
    db_session, table_factory, user_factory
):
    table = await table_factory()
    user = await user_factory()

    first_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )
    second_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(19, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )

    db_session.add_all([first_booking, second_booking])
    await db_session.commit()

    assert first_booking.id is not None
    assert second_booking.id is not None


async def test_identical_time_range_on_different_tables_is_allowed(
    db_session, table_factory, user_factory
):
    table_1 = await table_factory(number="A1")
    table_2 = await table_factory(number="B1")
    user = await user_factory()

    first_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table_1.id,
        user_id=user.id,
    )
    second_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table_2.id,
        user_id=user.id,
    )

    db_session.add_all([first_booking, second_booking])
    await db_session.commit()

    assert first_booking.id is not None
    assert second_booking.id is not None


async def test_time_range_generated_column_matches_expected_booked_window(
    db_session, table_factory, user_factory
):
    table = await table_factory()
    user = await user_factory()

    booking_date = date(2026, 10, 6)
    start_time = time(18, 0)
    slot_count = 2

    booking = BookingModel(
        booking_date=booking_date,
        start_time=start_time,
        slot_count=slot_count,
        table_id=table.id,
        user_id=user.id,
    )

    db_session.add(booking)
    await db_session.commit()
    await db_session.refresh(booking)

    expected_start = datetime.combine(booking_date, start_time)
    expected_end = expected_start + timedelta(minutes=slot_count * 30)

    assert booking.time_range.lower == expected_start
    assert booking.time_range.upper == expected_end


async def test_two_non_overlapping_bookings_on_same_table_succeed(
    db_session, table_factory, user_factory
):
    table = await table_factory(number="D1")
    user = await user_factory()

    morning_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(12, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )
    late_booking = BookingModel(
        booking_date=date(2026, 10, 6),
        start_time=time(18, 0),
        slot_count=2,
        table_id=table.id,
        user_id=user.id,
    )

    db_session.add_all([morning_booking, late_booking])
    await db_session.commit()

    assert morning_booking.id is not None
    assert late_booking.id is not None
