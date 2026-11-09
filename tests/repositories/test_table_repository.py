from datetime import time
from uuid import uuid4

from models.orm.city import CityModel
from models.orm.restaurant import RestaurantModel
from models.orm.table import TableModel
from repositories import TableRepository


async def test_table_repository_crud(db_session):
    city = CityModel(
        name=f"City {uuid4().hex}",
        country_code="UA",
        timezone="Europe/Kyiv",
    )
    suffix = uuid4().hex
    restaurant = RestaurantModel(
        email=f"restaurant-{suffix}@example.com",
        phone=f"+1{suffix[:10]}",
        name=f"Restaurant {suffix}",
        description="Repository test",
        opens_at=time(9, 0),
        closes_at=time(22, 0),
        address="1 Test Street",
        city=city,
    )
    db_session.add(restaurant)
    await db_session.flush()

    repository = TableRepository(db_session)
    table = TableModel(number="A1", capacity=4, restaurant_id=restaurant.id)

    created = await repository.create_new_table(table)
    assert created.id is not None
    assert await repository.get_table_by_id(created.id) is created
    assert await repository.get_table_by_id(-1) is None

    created.capacity = 6
    assert await repository.update_table(created) is created
    await repository.delete_table(created)
    assert await repository.get_table_by_id(created.id) is None
