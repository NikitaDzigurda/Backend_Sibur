from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from starlette import status

from app.users.user_profile.admin.repository import AdminRequiredException, UserAlreadyExistsException
from app.users.user_profile.schema import UserCreateSchema
from app.users.user_profile.admin.service import UserService

from app.dependency import *

router = APIRouter(prefix="/admin/users")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
    admin_payload: Annotated[dict, Depends(get_current_admin_user)]
):
    try:
        new_user = await user_service.create_user(
            admin_login=admin_payload["sub"],
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