import uvicorn
from fastapi import FastAPI

from app.users.user_profile.admin.handlers import router as user_router
from app.users.auth.handlers import router as auth_router
from app.chemicals.handlers_ch_operations.user_handlers import router as user_ch_operation_router
from app.chemicals.handlers_ch_operations.admin_handlers import router as admin_ch_operation_router

app = FastAPI(redoc_url=None)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(user_ch_operation_router)
app.include_router(admin_ch_operation_router)



# def run_app():
#     import uvicorn
#     uvicorn.run(
#         "app.main:app",
#         host='localhost',
#         port=5432,
#         reload=True,
#     )
#
#
# if __name__ == '__main__':
#     run_app()