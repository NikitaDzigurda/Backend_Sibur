from sqlalchemy import insert, select
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError

from app.users.user_profile.model import UserProfile
from app.users.user_profile.schema import UserCreateSchema

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class UserAlreadyExistsException(Exception):
    pass


class AdminRequiredException(Exception):
    pass


@dataclass
class UserRepository:
    db_session: AsyncSession

    async def get_user(self, user_id: str) -> UserProfile | None:
        result = await self.db_session.execute(
            select(UserProfile).where(UserProfile.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_login(self, login: str) -> UserProfile | None:
        result = await self.db_session.execute(
            select(UserProfile).where(UserProfile.login == login)
        )
        return result.scalar_one_or_none()

    async def get_user_role(self, login: str) -> str:
        user = await self.get_user_by_login(login)
        if not user:
            raise ValueError(f"User {login} not found")
        return user.role

    async def create_user(self, user_data: UserCreateSchema) -> UserProfile:
        try:
            result = await self.db_session.execute(
                insert(UserProfile).values(
                    login=user_data.login,
                    hashed_password=bcrypt_context.hash(user_data.password),
                    role=user_data.role,
                    user_data=user_data.user_data
                ).returning(UserProfile)
            )
            await self.db_session.commit()
            return result.scalar_one()
        except IntegrityError:
            await self.db_session.rollback()
            raise UserAlreadyExistsException(f"Login {user_data.login} already exists")


