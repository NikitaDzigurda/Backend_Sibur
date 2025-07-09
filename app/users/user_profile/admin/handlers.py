from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from starlette import status

from app.users.user_profile.admin.repository import AdminRequiredException, UserAlreadyExistsException
from app.users.user_profile.schema import UserCreateSchema
from app.users.user_profile.admin.service import UserService

from app.dependency import *

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin"]
                   )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
):
    try:
        new_user = await user_service.create_user(
            admin_login=admin_user.login,
            new_user_data=user_data
        )
        return {
            "message": "User created successfully",
            "login": new_user.login,
            "role": new_user.role
        }

    except AdminRequiredException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e))

    except UserAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))


@router.delete("/{user_login}", status_code=status.HTTP_204_NO_CONTENT)
async def del_user(
        user_service: Annotated[UserService, Depends(get_user_service)],
        admin_user: Annotated[UserProfile, Depends(get_current_admin_user)],
        user_login: str
):
    try:
        admin_login = admin_user.login
        await user_service.del_user_by_login(user_login, admin_login)

    except AdminRequiredException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e))