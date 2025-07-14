from pydantic_settings import BaseSettings

import os
import dotenv

dotenv.load_dotenv()


class Settings(BaseSettings):
    HOST: str = os.getenv("DB_HOST") if os.getenv("DB_HOST") is not None else "db"
    DB_PORT: int = 5432
    DB_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = '1234'
    DB_DRIVER: str = 'postgresql+asyncpg'
    DB_NAME: str = 'SIBUR_DB'

    JWT_SECRET_KEY: str = '071b4a3ac28a5678e2f60b0fad71b26b2689295cd75c83c945c54913391e8d6b'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    def get_url(self, is_async=True):
        if is_async:
            return f"{self.DB_DRIVER}://{self.DB_USER}:{self.POSTGRES_PASSWORD}@{self.HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"postgresql+psycopg2://{self.DB_USER}:{self.POSTGRES_PASSWORD}@{self.HOST}:{self.DB_PORT}/{self.DB_NAME}"

