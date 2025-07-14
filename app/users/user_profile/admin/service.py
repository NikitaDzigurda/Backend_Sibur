from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from starlette import status

from app.users.user_profile.admin.repository import UserRepository, UserAlreadyExistsException, AdminRequiredException
from app.users.user_profile.model import UserProfile
from app.users.user_profile.schema import UserCreateSchema
from app.users.auth.service import AuthService
from fastapi import HTTPException


@dataclass
class UserService:
    user_repository: UserRepository
    auth_service: AuthService

    async def create_user(self,
                          admin_login: str,
                          new_user_data: UserCreateSchema) -> UserProfile:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        if await self.user_repository.get_user_by_login(new_user_data.login):
            raise UserAlreadyExistsException(f"User {new_user_data.login} already exists")

        return await self.user_repository.create_user(new_user_data)

    async def get_user_from_token(self, token: str) -> UserProfile:

        payload = await self.auth_service.verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing user_id")

        user = await self.user_repository.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    async def del_user_by_login(self, user_login: str, admin_login: str):
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can delete users")

        try:
            deleted = await self.user_repository.del_user_by_login(user_login)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with login '{user_login}' not found"
                )
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database operation failed"
            )
