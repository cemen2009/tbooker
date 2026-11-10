from uuid import uuid4

from models.orm.city import CityModel
from repositories import CityRepository


async def test_city_repository_crud(db_session):
    repository = CityRepository(db_session)
    city = CityModel(
        name=f"City {uuid4().hex}",
        country_code="UA",
        timezone="Europe/Kyiv",
    )

    created = await repository.create_new_city(city)
    assert created.id is not None
    assert await repository.get_city_by_id(created.id) is created
    assert await repository.get_city_by_id(-1) is None

    created.name = "Updated City"
    assert await repository.update_city(created) is created
    await repository.delete_city(created)
    assert await repository.get_city_by_id(created.id) is None
