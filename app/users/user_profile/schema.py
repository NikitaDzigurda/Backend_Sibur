from pydantic import BaseModel, Field


class UserCreateSchema(BaseModel):
    login: str = Field(...)
    password: str = Field(...)
    role: str = Field(default="user")
    user_data: str = Field(...)
