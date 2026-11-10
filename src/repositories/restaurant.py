from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orm.restaurant import RestaurantModel


class RestaurantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_restaurant_and_dont_commit(
        self, restaurant: RestaurantModel
    ) -> RestaurantModel:
        self.session.add(restaurant)
        await self.session.flush()
        return restaurant

    async def create_new_restaurant(
        self, restaurant: RestaurantModel
    ) -> RestaurantModel:
        await self.create_new_restaurant_and_dont_commit(restaurant)
        await self.session.commit()
        return restaurant

    async def get_restaurant_by_id(self, restaurant_id: int) -> RestaurantModel | None:
        statement = select(RestaurantModel).where(RestaurantModel.id == restaurant_id)
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def update_restaurant_and_dont_commit(
        self, restaurant: RestaurantModel
    ) -> RestaurantModel:
        await self.session.flush()
        return restaurant

    async def update_restaurant(self, restaurant: RestaurantModel) -> RestaurantModel:
        await self.update_restaurant_and_dont_commit(restaurant)
        await self.session.commit()
        return restaurant

    async def delete_restaurant_and_dont_commit(
        self, restaurant: RestaurantModel
    ) -> None:
        await self.session.delete(restaurant)
        await self.session.flush()

    async def delete_restaurant(self, restaurant: RestaurantModel) -> None:
        await self.delete_restaurant_and_dont_commit(restaurant)
        await self.session.commit()
