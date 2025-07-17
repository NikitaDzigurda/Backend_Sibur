from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.users.user_profile.admin.handlers import router as user_router
from app.users.auth.handlers import router as auth_router
from app.chemicals.handlers_ch_operations.user_handlers import router as user_ch_operation_router
from app.chemicals.handlers_ch_operations.admin_handlers import router as admin_ch_operation_router

app = FastAPI(redoc_url=None)

origins = ["*"]
middleware = CORSMiddleware(
    app=app,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(user_ch_operation_router)
app.include_router(admin_ch_operation_router)

