from dataclasses import dataclass
from app.users.user_profile.admin.repository import UserRepository, UserAlreadyExistsException, AdminRequiredException
from app.users.user_profile.model import UserProfile
from app.users.user_profile.schema import UserCreateSchema


@dataclass
class UserService:
    user_repository: UserRepository

    async def create_user(self,
                          admin_login: str,
                          new_user_data: UserCreateSchema) -> UserProfile:
        admin_role = await self.user_repository.get_user_role(admin_login)
        if admin_role != "admin":
            raise AdminRequiredException("Only admin can create users")

        if await self.user_repository.get_user_by_login(new_user_data.login):
            raise UserAlreadyExistsException(f"User {new_user_data.login} already exists")

        return await self.user_repository.create_user(new_user_data)