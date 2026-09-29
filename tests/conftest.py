import asyncio

from alembic import command
from alembic.config import Config
import pytest
from testcontainers.community.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


@pytest.fixture(scope="module")
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
    async_engine = create_async_engine(test_db_async_url)

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