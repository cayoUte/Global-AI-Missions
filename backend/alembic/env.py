"""Alembic environment. Online migrations only (we always have a database to talk to).

URL precedence: `sqlalchemy.url` set on the Config (tests) > `-x url=...` > DATABASE_URL from
app.core.config (the only reader of environment variables).
"""

from sqlalchemy import create_engine, pool

from alembic import context
from app.core.config import get_settings
from app.models import Base

config = context.config
target_metadata = Base.metadata


def database_url() -> str:
    return (
        config.get_main_option("sqlalchemy.url")
        or context.get_x_argument(as_dictionary=True).get("url")
        or get_settings().database_url
    )


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise SystemExit("Offline mode is not supported: run against a database.")
run_migrations_online()
