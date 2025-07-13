from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import core_config


class BaseDBModel(DeclarativeBase):
    pass


engine = create_async_engine(core_config.ASYNC_DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
