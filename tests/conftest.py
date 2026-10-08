import asyncio
from datetime import time
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from models.db.city import CityModel
from models.db.restaurant import RestaurantModel
from models.db.table import TableModel
from models.db.user import UserModel, UserRole, UserStatus


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:18") as container:
        yield container


@pytest.fixture(scope="session")
def test_db_async_url(postgres_container) -> str:
    url = postgres_container.get_connection_url()
    async_url = url.replace("postgresql+psycopg2", "postgresql+asyncpg")
    return async_url


@pytest.fixture(scope="session")
async def db_engine(test_db_async_url):

    # asyncEngine may be used across different event loops in tests.
    # NullPool prevents connections created in one loop from being reused in another
    async_engine = create_async_engine(test_db_async_url, poolclass=NullPool)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_async_url)

    def _upgrade():
        command.upgrade(alembic_cfg, "head")

    def _downgrade():
        command.downgrade(alembic_cfg, "base")

    await asyncio.to_thread(_upgrade)

    yield async_engine

    await asyncio.to_thread(_downgrade)
    await async_engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def table_factory(db_session):
    async def create_table(number: str | None = None):
        suffix = uuid4().hex
        city = CityModel(name=f"Test City {suffix}", country_code="TC", timezone="UTC")
        restaurant = RestaurantModel(
            email=f"restaurant-{suffix}@example.com",
            phone=f"+1{suffix[:10]}",
            name=f"Test Restaurant {suffix}",
            description="Test restaurant",
            opens_at=time(9, 0),
            closes_at=time(22, 0),
            address="1 Test Street",
            city=city,
        )
        table = TableModel(
            number=number or f"T-{suffix[:8]}",
            capacity=4,
            restaurant=restaurant,
        )
        db_session.add(table)
        await db_session.flush()
        return table

    return create_table


@pytest.fixture
async def user_factory(db_session):
    async def create_user():
        suffix = uuid4().hex
        user = UserModel(
            email=f"user-{suffix}@example.com",
            hashed_password="test-password-hash",
            first_name="Test",
            last_name="User",
            role=UserRole.user,
            status=UserStatus.active,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return create_user
