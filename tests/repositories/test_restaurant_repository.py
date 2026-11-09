from datetime import time
from uuid import uuid4

from models.orm.city import CityModel
from models.orm.restaurant import RestaurantModel
from repositories import RestaurantRepository


async def test_restaurant_repository_crud(db_session):
    city = CityModel(
        name=f"City {uuid4().hex}",
        country_code="UA",
        timezone="Europe/Kyiv",
    )
    db_session.add(city)
    await db_session.flush()

    repository = RestaurantRepository(db_session)
    suffix = uuid4().hex
    restaurant = RestaurantModel(
        email=f"restaurant-{suffix}@example.com",
        phone=f"+1{suffix[:10]}",
        name=f"Restaurant {suffix}",
        description="Repository test",
        opens_at=time(9, 0),
        closes_at=time(22, 0),
        address="1 Test Street",
        city_id=city.id,
    )

    created = await repository.create_new_restaurant(restaurant)
    assert created.id is not None
    assert await repository.get_restaurant_by_id(created.id) is created
    assert await repository.get_restaurant_by_id(-1) is None

    created.name = "Updated Restaurant"
    assert await repository.update_restaurant(created) is created
    await repository.delete_restaurant(created)
    assert await repository.get_restaurant_by_id(created.id) is None
