from pydantic_settings import BaseSettings
import os
import dotenv

dotenv.load_dotenv()


class Settings(BaseSettings):
    HOST: str = os.getenv("DB_HOST", "amvera-ghataju-cnpg-sibur-project-db-rw")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))
    DB_USER: str = os.getenv("DB_USER", "sibur")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "jjb-ZVT-ViG-X9B")
    DB_DRIVER: str = os.getenv("DB_DRIVER", "postgresql+asyncpg")
    DB_NAME: str = os.getenv("DB_NAME", "SIBUR_DB")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "071b4a3ac28a5678e2f60b0fad71b26b2689295cd75c83c945c54913391e8d6b")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))

    def get_url(self, is_async=True):
        if is_async:
            return f"{self.DB_DRIVER}://{self.DB_USER}:{self.POSTGRES_PASSWORD}@{self.HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            return f"postgresql+psycopg2://{self.DB_USER}:{self.POSTGRES_PASSWORD}@{self.HOST}:{self.DB_PORT}/{self.DB_NAME}"