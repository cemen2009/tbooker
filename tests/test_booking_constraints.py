import pytest

from sqlalchemy.exc import IntegrityError


async def test_overlapping_booking_rejected(db_session, table_factory, user_factory):
    ...
