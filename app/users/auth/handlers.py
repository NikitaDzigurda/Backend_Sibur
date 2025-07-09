from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from app.users.auth.service import AuthService
from app.users.auth.schema import TokenResponse, UserLoginRequest
from app.dependency import get_auth_service, oauth2_scheme

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


@router.get("/verify")
async def verify_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    try:
        payload = await auth_service.verify_token(token)
        return {
            "is_valid": True,
            "user_id": payload.get("user_id"),
            "role": payload.get("role"),
            "expires": payload.get("exp")
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"is_valid": False, "detail": e.detail}
        )