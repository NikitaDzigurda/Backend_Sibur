from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.infrastructure import get_db_session
from app.settings import Settings
from app.users.auth.service import AuthService
from app.users.user_profile.admin import UserRepository, UserService
from app.chemicals.repository import ChemicalRepository
from app.chemicals.service import ChemicalService
from app.users.user_profile.model import UserProfile

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_user_repository(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> UserRepository:
    return UserRepository(db_session=db_session)

async def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    try:
        settings = Settings()
        if not settings.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY is missing in settings")

        return AuthService(user_repository=user_repository,
                           settings=settings
                           )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth service initialization failed: {str(e)}")


async def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserService:
    return UserService(user_repository=user_repository, auth_service=auth_service)


async def get_chemical_repository(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> ChemicalRepository:
    return ChemicalRepository(db_session=db_session)


async def get_chemical_service(
        chemical_repository: Annotated[ChemicalRepository, Depends(get_chemical_repository)]
) -> ChemicalService:
    return ChemicalService(chemical_repository=chemical_repository)


async def get_current_admin_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserProfile:
    user = await user_service.get_user_from_token(token)

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )

    return user


async def get_current_user(
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_token: Annotated[str, Depends(oauth2_scheme)]
):
    return await user_service.get_user_from_token(auth_token)
