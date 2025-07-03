from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.infrastructure import get_db_session
from app.settings import Settings
from app.users.auth.service import AuthService
from app.users.user_profile.admin import UserRepository, UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_user_repository(db_session: Annotated[AsyncSession, Depends(get_db_session)]) -> UserRepository:
    return UserRepository(db_session=db_session)


async def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repository=user_repository)


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


async def get_current_admin_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    payload = await auth_service.verify_token(token)
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return payload