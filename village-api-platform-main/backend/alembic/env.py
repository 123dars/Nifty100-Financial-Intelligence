import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add parent directory to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env from the backend directory
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.config import settings
from app.database import Base
from app.models import Country, State, District, SubDistrict, Village, ApiKey, User, RequestLog  # noqa: F401

# Alembic Config object
config = context.config

# Interpret config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url with a sync connection string (psycopg2)
from urllib.parse import parse_qs, urlparse, urlunparse

db_url = settings.DATABASE_URL
parsed = urlparse(db_url)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop("sslmode", ["require"])[0]
clean_url = urlunparse(parsed._replace(scheme="postgresql+psycopg2", query=""))
db_url = f"{clean_url}?sslmode={ssl_mode}"

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


try:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
except Exception as e:
    print(f"Alembic migration error: {e}")
    raise
