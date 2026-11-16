from unittest.mock import AsyncMock

import pytest

from common.exceptions.repository import DuplicateEntityError
from common.exceptions.service import UserAlreadyExistsError, UserNotFoundError
from core.security import Hasher
from models.orm import UserModel, UserRole, UserStatus
from models.schemas.user import UserCreate, UserPatch
from repositories import UserRepository
from services.user import UserService


@pytest.fixture
def user_service():
    service = UserService(AsyncMock())
    service.user_repository = AsyncMock(spec=UserRepository)
    return service


def build_user(email: str = "alex@example.com") -> UserModel:
    return UserModel(
        id=1,
        email=email,
        _hashed_password="test-password-hash",
        first_name="Alex",
        last_name="Smith",
        role=UserRole.user,
        status=UserStatus.active,
    )


async def test_get_user_by_id_raises_not_found(user_service):
    user_service.user_repository.get_user_by_id.return_value = None

    with pytest.raises(UserNotFoundError) as error:
        await user_service.get_user_by_id(42)

    assert str(error.value) == "User not found"


async def test_create_user_sets_server_managed_fields_and_hashes_password(user_service):
    user_service.user_repository.get_user_by_email.return_value = None
    user_service.user_repository.create_new_user.side_effect = lambda user: user
    data = UserCreate(
        email="Alex@example.com",
        password="TbookerExample9!",
        first_name="Alex",
        last_name="Smith",
    )

    user = await user_service.create_user(data)

    assert user.email == "alex@example.com"
    assert user.role is UserRole.user
    assert user.status is UserStatus.active
    assert user._hashed_password != data.password
    assert Hasher.is_valid_password(data.password, user._hashed_password)


async def test_create_user_rejects_duplicate_email(user_service):
    user_service.user_repository.get_user_by_email.return_value = build_user()
    data = UserCreate(
        email="alex@example.com",
        password="TbookerExample9!",
        first_name="Alex",
        last_name="Smith",
    )

    with pytest.raises(UserAlreadyExistsError):
        await user_service.create_user(data)

    user_service.user_repository.create_new_user.assert_not_awaited()


async def test_create_user_translates_repository_duplicate(user_service):
    user_service.user_repository.get_user_by_email.return_value = None
    user_service.user_repository.create_new_user.side_effect = DuplicateEntityError(
        "duplicate"
    )
    data = UserCreate(
        email="alex@example.com",
        password="TbookerExample9!",
        first_name="Alex",
        last_name="Smith",
    )

    with pytest.raises(UserAlreadyExistsError):
        await user_service.create_user(data)


async def test_update_user_applies_only_provided_fields(user_service):
    user = build_user()
    user_service.user_repository.get_user_by_id.return_value = user
    user_service.user_repository.update_user.return_value = user

    updated_user = await user_service.update_user(
        1, UserPatch(first_name="Alexandra")
    )

    assert updated_user.first_name == "Alexandra"
    assert updated_user.last_name == "Smith"
    user_service.user_repository.update_user.assert_awaited_once_with(user)


async def test_get_users_list_builds_paginated_response(user_service):
    user_service.user_repository.get_paginated_users.return_value = (
        [build_user()],
        21,
    )

    users_page = await user_service.get_users_list(
        search_word=" Alex ",
        status=UserStatus.active,
        page=1,
        per_page=20,
    )

    assert users_page.total == 21
    assert users_page.next_page == (
        "/users?page=2&per_page=20&search_word=Alex&status=active"
    )
    assert users_page.prev_page is None
    assert users_page.last_page == (
        "/users?page=2&per_page=20&search_word=Alex&status=active"
    )


async def test_get_empty_users_list_has_no_last_page(user_service):
    user_service.user_repository.get_paginated_users.return_value = ([], 0)

    users_page = await user_service.get_users_list()

    assert users_page.total_pages == 0
    assert users_page.last_page is None
