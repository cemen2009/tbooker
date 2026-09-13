import pytest
from dotenv import load_dotenv

from core.config import get_settings


@pytest.mark.parametrize(
    "env_name, expected_db_host, expected_db_name, expected_redis_host, expected_ttl",
    [
        ("dev", "localhost", "tbooker", "localhost", 30),
        ("prod", "prod-db", "tbooker_prod", "prod-redis", 60),
    ],
)
def test_settings_loads_by_environment(
    monkeypatch,
    tmp_path,
    env_name,
    expected_db_host,
    expected_db_name,
    expected_redis_host,
    expected_ttl,
):
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()

    for key in (
        "ENVIRONMENT",
        "DEBUG",
        "DB__HOST",
        "DB__PORT",
        "DB__USER",
        "DB__PASSWORD",
        "DB__NAME",
        "REDIS__HOST",
        "REDIS__PORT",
        "REDIS__TTL_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)

    env_file = tmp_path / f".env.{env_name}"
    env_file.write_text(
        "\n".join(
            [
                f"ENVIRONMENT={env_name}",
                "DEBUG=true",
                f"DB__HOST={expected_db_host}",
                "DB__PORT=5432",
                "DB__USER=app",
                "DB__PASSWORD=app",
                f"DB__NAME={expected_db_name}",
                f"REDIS__HOST={expected_redis_host}",
                "REDIS__PORT=6379",
                f"REDIS__TTL_SECONDS={expected_ttl}",
                "",
            ]
        )
    )

    load_dotenv(env_file, override=True)
    settings = get_settings()

    assert settings.environment == env_name
    assert settings.db.host == expected_db_host
    assert settings.db.name == expected_db_name
    assert settings.redis.host == expected_redis_host
    assert settings.redis.ttl_seconds == expected_ttl
