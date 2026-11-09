from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orm.city import CityModel


class CityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_city_and_dont_commit(self, city: CityModel) -> CityModel:
        self.session.add(city)
        await self.session.flush()
        return city

    async def create_new_city(self, city: CityModel) -> CityModel:
        await self.create_new_city_and_dont_commit(city)
        await self.session.commit()
        return city

    async def get_city_by_id(self, city_id: int) -> CityModel | None:
        statement = select(CityModel).where(CityModel.id == city_id)
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def update_city(self, city: CityModel) -> CityModel:
        await self.session.flush()
        return city

    async def delete_city(self, city: CityModel) -> None:
        await self.session.delete(city)
        await self.session.flush()
