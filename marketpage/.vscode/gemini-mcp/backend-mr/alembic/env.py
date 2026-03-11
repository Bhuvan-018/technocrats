import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

config = __import__("alembic.config").config.Config("alembic.ini")
fileConfig(config.config_file_name)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sa_db import Base, DATABASE_URL
import models  # noqa: F401

target_metadata = Base.metadata


def get_url() -> str:
    return os.environ.get("DATABASE_URL", DATABASE_URL)


def run_migrations_offline():
    url = get_url()
    context = __import__("alembic.context").context
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    context = __import__("alembic.context").context
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if __name__ == "__main__":
    run_migrations_online()
