from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from common.exceptions.repository import DuplicateEntityError
from models.orm import UserModel, UserStatus


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_user_and_dont_commit(self, user: UserModel) -> UserModel:
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as error:
            await self._handle_integrity_error(error)
        return user

    async def create_new_user(self, user: UserModel) -> UserModel:
        await self.create_new_user_and_dont_commit(user)
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self._handle_integrity_error(error)
        return user

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def get_user_by_email(self, email: str) -> UserModel | None:
        statement = select(UserModel).where(UserModel.email == email.lower())
        result = await self.session.scalars(statement)
        return result.one_or_none()

    async def get_paginated_users(
        self,
        search_word: str | None = None,
        status: UserStatus | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[UserModel], int]:
        if page < 1:
            raise ValueError("page must be greater than or equal to 1")
        if per_page < 1:
            raise ValueError("per_page must be greater than or equal to 1")

        where_clauses: list[ColumnElement[bool]] = []
        if status is not None:
            where_clauses.append(UserModel.status == status)

        if search_word is not None and (search := search_word.strip()):
            escaped_search = (
                search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            )
            search_pattern = f"%{escaped_search}%"
            where_clauses.append(
                or_(
                    UserModel.email.ilike(search_pattern, escape="\\"),
                    UserModel.first_name.ilike(search_pattern, escape="\\"),
                    UserModel.last_name.ilike(search_pattern, escape="\\"),
                )
            )

        count_statement = (
            select(func.count(UserModel.id))
            .where(*where_clauses)
        )
        total = (await self.session.execute(count_statement)).scalar_one()

        statement = (
            select(UserModel)
            .where(*where_clauses)
            .order_by(*UserModel.order_by())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.session.scalars(statement)
        return list(result.all()), total

    async def update_user_and_dont_commit(self, user: UserModel) -> UserModel:
        try:
            await self.session.flush()
        except IntegrityError as error:
            await self._handle_integrity_error(error)
        return user

    async def update_user(self, user: UserModel) -> UserModel:
        await self.update_user_and_dont_commit(user)
        try:
            await self.session.commit()
        except IntegrityError as error:
            await self._handle_integrity_error(error)
        return user

    async def _handle_integrity_error(self, error: IntegrityError) -> None:
        await self.session.rollback()
        if self._is_email_unique_violation(error):
            raise DuplicateEntityError(
                "A user with this email already exists"
            ) from error
        raise error

    @staticmethod
    def _is_email_unique_violation(error: IntegrityError) -> bool:
        original_error: BaseException | None = error.orig
        visited: set[int] = set()
        while original_error is not None and id(original_error) not in visited:
            visited.add(id(original_error))
            constraint_name = getattr(original_error, "constraint_name", None)
            if constraint_name is None:
                diagnostic = getattr(original_error, "diag", None)
                constraint_name = getattr(diagnostic, "constraint_name", None)
            if constraint_name == "users_email_key":
                return True

            cause = original_error.__cause__ or original_error.__context__
            nested_error = getattr(original_error, "orig", None)
            original_error = (
                nested_error
                if isinstance(nested_error, BaseException)
                else cause
            )
        return False

    async def delete_user_and_dont_commit(self, user: UserModel) -> None:
        await self.session.delete(user)
        await self.session.flush()

    async def delete_user(self, user: UserModel) -> None:
        await self.delete_user_and_dont_commit(user)
        await self.session.commit()
