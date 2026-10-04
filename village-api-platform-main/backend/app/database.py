from urllib.parse import parse_qs, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


def _build_engine_url(url: str) -> tuple[str, dict]:
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    ssl_mode = query_params.pop("sslmode", ["require"])[0]
    query_params.pop("channel_binding", None)

    scheme = "postgresql+asyncpg"
    clean_url = urlunparse(parsed._replace(scheme=scheme, query=""))

    connect_args = {"ssl": ssl_mode, "statement_cache_size": 0}
    return clean_url, connect_args


_db_url, _connect_args = _build_engine_url(settings.DATABASE_URL)
engine = create_async_engine(
    _db_url,
    echo=False,
    connect_args=_connect_args,
    poolclass=NullPool,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
