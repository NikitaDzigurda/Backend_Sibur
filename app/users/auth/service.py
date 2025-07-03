from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from typing import Optional

from app.settings import Settings
from app.users.user_profile.admin.repository import UserRepository
from app.users.user_profile.model import UserProfile
from app.users.auth.schema import TokenResponse


@dataclass
class AuthService:
    user_repository: UserRepository
    settings: Settings
    pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def authenticate_user(self, username: str, password: str) -> UserProfile:
        user = await self.user_repository.get_user_by_login(username)
        self._validate_user_credentials(user, password)
        return user

    async def create_access_token(self, user: UserProfile) -> str:
        payload = {
            "sub": user.login,
            "user_id": user.id,
            "role": user.role,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM
        )

    async def login_with_form(self, form_data: OAuth2PasswordRequestForm) -> TokenResponse:
        user = await self.authenticate_user(form_data.username, form_data.password)
        return TokenResponse(
            access_token=await self.create_access_token(user),
            token_type="bearer"
        )

    async def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            if datetime.fromtimestamp(payload["exp"], tz=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
            return payload
        except JWTError:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    def _validate_user_credentials(self, user: Optional[UserProfile], password: str):
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        if not self.pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")