from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.orm.table import TableModel


class TableRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_table_and_dont_commit(self, table: TableModel) -> TableModel:
        self.session.add(table)
        await self.session.flush()
        return table

    async def create_new_table(self, table: TableModel) -> TableModel:
        await self.create_new_table_and_dont_commit(table)
        await self.session.commit()
        return table

    async def get_table_by_id(self, table_id: int) -> TableModel | None:
        statement = select(TableModel).where(TableModel.id == table_id)
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def update_table(self, table: TableModel) -> TableModel:
        await self.session.flush()
        return table

    async def delete_table(self, table: TableModel) -> None:
        await self.session.delete(table)
        await self.session.flush()
