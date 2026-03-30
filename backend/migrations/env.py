from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os, sys
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db.base import Base
from backend.config import get_settings
import backend.models  # noqa: ensure all models registered

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_db_url() -> str:
    url = get_settings().database_url
    if "+asyncpg" in url:
        sync_url = url.replace("+asyncpg", "+psycopg2")
        parts = urlsplit(sync_url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "ssl" in query and "sslmode" not in query:
            query["sslmode"] = query.pop("ssl")
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    return url


def run_migrations_offline() -> None:
    url = _get_sync_db_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _get_sync_db_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
