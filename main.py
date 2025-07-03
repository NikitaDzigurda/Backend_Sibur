from fastapi import FastAPI

from app.users.user_profile.admin.handlers import router as user_router
from app.users.auth.handlers import router as auth_router

app = FastAPI(redoc_url=None)

app.include_router(user_router)
app.include_router(auth_router)