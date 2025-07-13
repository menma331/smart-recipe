import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_USER = os.getenv("POSTGRES_USER", "recipe_user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "recipe_pass")
    DB_NAME = os.getenv("POSTGRES_DB", "recipe_db")

    ASYNC_DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SYNC_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


core_config = Config()
