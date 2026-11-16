from math import ceil
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions.repository import DuplicateEntityError
from common.exceptions.service import UserAlreadyExistsError, UserNotFoundError
from models.orm import UserModel, UserRole, UserStatus
from models.schemas.user import (
    UserCreate,
    UserListItemResponse,
    UserListResponse,
    UserPatch,
    UserPut,
)
from repositories import UserRepository


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.user_repository = UserRepository(db)

    async def get_user_by_id(self, user_id: int) -> UserModel:
        user = await self.user_repository.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    async def get_user_by_email(self, email: str) -> UserModel:
        user = await self.user_repository.get_user_by_email(email)
        if user is None:
            raise UserNotFoundError("User not found")
        return user

    async def get_users_list(
        self,
        search_word: str | None = None,
        status: UserStatus | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> UserListResponse:
        users, total = await self.user_repository.get_paginated_users(
            search_word=search_word,
            status=status,
            page=page,
            per_page=per_page,
        )

        last_page = ceil(total / per_page)
        return UserListResponse(
            items=[UserListItemResponse.model_validate(user) for user in users],
            total=total,
            current_page=page,
            per_page=per_page,
            next_page=(
                self._users_page_url(page + 1, per_page, search_word, status)
                if page < last_page
                else None
            ),
            prev_page=(
                self._users_page_url(page - 1, per_page, search_word, status)
                if page > 1
                else None
            ),
            first_page=self._users_page_url(1, per_page, search_word, status),
            last_page=(
                self._users_page_url(last_page, per_page, search_word, status)
                if last_page
                else None
            ),
        )

    async def create_user(self, data: UserCreate) -> UserModel:
        return await self._create_user(data, commit=True)

    async def create_user_without_commit(self, data: UserCreate) -> UserModel:
        return await self._create_user(data, commit=False)

    async def update_user(
        self, user_id: int, payload: UserPut | UserPatch
    ) -> UserModel:
        user = await self.get_user_by_id(user_id)
        update_data = payload.model_dump(exclude_unset=True)

        if "email" in update_data:
            existing_user = await self.user_repository.get_user_by_email(
                update_data["email"]
            )
            if existing_user is not None and existing_user.id != user.id:
                raise UserAlreadyExistsError(
                    "A user with this email already exists"
                )

        for field, value in update_data.items():
            setattr(user, field, value)

        try:
            return await self.user_repository.update_user(user)
        except DuplicateEntityError as error:
            raise UserAlreadyExistsError(
                "A user with this email already exists"
            ) from error

    async def _create_user(self, data: UserCreate, *, commit: bool) -> UserModel:
        existing_user = await self.user_repository.get_user_by_email(data.email)
        if existing_user is not None:
            raise UserAlreadyExistsError("A user with this email already exists")

        user = UserModel(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            role=UserRole.user,
            status=UserStatus.active,
            city_id=data.city_id,
        )
        user.password = data.password

        try:
            if commit:
                return await self.user_repository.create_new_user(user)
            return await self.user_repository.create_new_user_and_dont_commit(user)
        except DuplicateEntityError as error:
            raise UserAlreadyExistsError(
                "A user with this email already exists"
            ) from error

    @staticmethod
    def _users_page_url(
        page: int,
        per_page: int,
        search_word: str | None,
        status: UserStatus | None,
    ) -> str:
        query_parameters: list[tuple[str, str | int]] = [
            ("page", page),
            ("per_page", per_page),
        ]
        if search_word is not None and search_word.strip():
            query_parameters.append(("search_word", search_word.strip()))
        if status is not None:
            query_parameters.append(("status", status.value))
        return f"/users?{urlencode(query_parameters)}"
