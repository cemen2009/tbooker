from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models.orm.user import UserModel, UserRole, UserStatus
from repositories.repository import UserRepository


def build_user(email: str, *, first_name: str, status: UserStatus) -> UserModel:
    return UserModel(
        email=email,
        hashed_password="test-password-hash",
        first_name=first_name,
        last_name="Repository",
        role=UserRole.user,
        status=status,
    )


async def test_user_repository_crud(db_session):
    repository = UserRepository(db_session)
    user = build_user(
        f"user-{uuid4().hex}@example.com",
        first_name="Create",
        status=UserStatus.active,
    )

    created = await repository.create_user(user)
    assert created.id is not None
    assert await repository.get_user_by_id(created.id) is created
    assert await repository.get_user_by_email(created.email) is created

    created.first_name = "Updated"
    await repository.update_user(created)
    assert created.first_name == "Updated"

    await repository.delete_user(created)
    assert await repository.get_user_by_id(created.id) is None


async def test_user_email_is_lowercase_and_case_insensitively_unique(db_session):
    repository = UserRepository(db_session)
    user = build_user(
        "Mixed.Case@example.com",
        first_name="Email",
        status=UserStatus.active,
    )

    assert user.email == "mixed.case@example.com"
    await repository.create_user(user)
    assert await repository.get_user_by_email("MIXED.CASE@EXAMPLE.COM") is user

    user.email = "Updated.Case@example.com"
    await repository.update_user(user)
    assert user.email == "updated.case@example.com"
    assert await repository.get_user_by_email("UPDATED.CASE@EXAMPLE.COM") is user

    duplicate = build_user(
        "UPDATED.CASE@EXAMPLE.COM",
        first_name="Duplicate",
        status=UserStatus.active,
    )
    with pytest.raises(IntegrityError):
        await repository.create_user(duplicate)
    await db_session.rollback()


async def test_database_rejects_non_lowercase_user_email(db_session):
    statement = text(
        "INSERT INTO users (email, password, first_name, last_name, role, status) "
        "VALUES (:email, :password, :first_name, :last_name, :role, :status)"
    )

    with pytest.raises(IntegrityError):
        await db_session.execute(
            statement,
            {
                "email": "Mixed.Case@example.com",
                "password": "test-password-hash",
                "first_name": "Email",
                "last_name": "Case",
                "role": "user",
                "status": "active",
            },
        )
    await db_session.rollback()


async def test_get_paginated_users_filters_and_orders(db_session):
    repository = UserRepository(db_session)
    search_token = uuid4().hex
    users = [
        build_user(
            f"{search_token}-c@example.com",
            first_name="Charlie",
            status=UserStatus.active,
        ),
        build_user(
            f"{search_token}-a@example.com",
            first_name="Alice",
            status=UserStatus.active,
        ),
        build_user(
            f"{search_token}-b@example.com",
            first_name="Bob",
            status=UserStatus.inactive,
        ),
    ]
    for user in users:
        await repository.create_user(user)

    first_page, total = await repository.get_paginated_users(
        search_word=search_token,
        status=UserStatus.active,
        page=1,
        per_page=1,
    )
    second_page, second_total = await repository.get_paginated_users(
        search_word=search_token,
        status=UserStatus.active,
        page=2,
        per_page=1,
    )

    assert total == second_total == 2
    assert [user.first_name for user in first_page] == ["Alice"]
    assert [user.first_name for user in second_page] == ["Charlie"]
