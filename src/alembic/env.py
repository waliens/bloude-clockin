import os
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context
from database import get_db_url
from models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config



# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    prefix = "sqlalchemy."
    options = dict(
        (key[len(prefix) :], configuration[key])
        for key in configuration
        if key.startswith(prefix)
    )
    options["_coerce_config"] = True
    options.update(poolclass=pool.NullPool)

    with_async = not os.getenv("NO_ASYNC", False)

    connectable = create_engine(get_db_url(with_async=with_async), **options)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
