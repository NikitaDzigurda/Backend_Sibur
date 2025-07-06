from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.users.auth.service import AuthService
from app.users.auth.schema import TokenResponse, UserLoginRequest
from app.dependency import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        user = await auth_service.authenticate_user(request.username, request.password)
        return TokenResponse(
            access_token=await auth_service.create_access_token(user),
            token_type="bearer",
        )
    except HTTPException as e:
        raise e


@router.post("/token", response_model=TokenResponse)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login_with_form(form_data)