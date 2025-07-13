import os
import subprocess
import time
import asyncio
from contextlib import asynccontextmanager

import psycopg2
import pytest
from dotenv import load_dotenv
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from api.recipes import recipes_router
from db_manager import RecipeDBManager

load_dotenv()

TEST_DB_URL = os.getenv("DATABASE_URL_TEST")
TEST_DB_URL_SYNC = os.getenv("DATABASE_URL_TEST_SYNC")
if not TEST_DB_URL or not TEST_DB_URL_SYNC:
    raise RuntimeError("Не заданы TEST_DB_URL или TEST_DB_URL_SYNC")


# 1) Асинхронный движок и фабрика сессий для тестов
async_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    isolation_level="REPEATABLE_READ"
)
AsyncTestSession = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@asynccontextmanager
async def scoped_async_session():
    async with AsyncTestSession() as session:
        yield session


# 2) Ждём БД и накатываем миграции перед сессией pytest
def wait_for_db(sync_url: str, timeout: int = 30):
    start = time.time()
    while True:
        try:
            conn = psycopg2.connect(sync_url)
            conn.close()
            return
        except Exception:
            if time.time() - start > timeout:
                raise RuntimeError("Timed out waiting for test DB")
            time.sleep(1)


def run_alembic_migrations():
    env = os.environ.copy()
    env["SQLALCHEMY_URL"] = TEST_DB_URL_SYNC
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        cwd=os.getcwd(),  # или путь к корню проекта
        env=env
    )


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    wait_for_db(TEST_DB_URL_SYNC)
    run_alembic_migrations()


# 3) Переключаемся на свой event loop для asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# 4) Фикстура чистки схемы после каждого теста
@pytest.fixture(autouse=True)
async def clean_db():
    yield
    async with async_engine.connect() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await conn.commit()


# 5) Фикстура с реальной сессией
@pytest.fixture
async def db_session():
    async with scoped_async_session() as session:
        yield session


# 6) Фикстура менеджера
@pytest.fixture
async def recipe_manager(db_session):
    # передаём лямбду или саму сессию – как ожидает конструктор
    return RecipeDBManager(session=lambda: db_session)


# 7) FastAPI app + httpx client для интеграционных тестов
@pytest.fixture(scope="session")
def app(db_session):
    app = FastAPI()
    # если у тебя endpoints используют глобальный recipe_manager,
    # можно вместо dependency_overrides прямо присвоить:
    # from api.recipes import recipe_manager as global_rm
    # global_rm.session = lambda: db_session
    app.include_router(recipes_router)
    return app


@pytest.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
