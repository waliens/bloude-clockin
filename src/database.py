import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from alembic.config import Config
from alembic import command


def get_db_url():
  username = os.getenv("POSTGRES_USER")
  password = os.getenv("POSTGRES_PASSWORD")
  host = os.getenv("POSTGRES_HOST")
  dbname = os.getenv("POSTGRES_DB")
  return "postgresql+asyncpg://{}:{}@{}/{}".format(username, password, host, dbname)


# async def add_raids(sess=None):
#     pass


# async def add_items(sess=None):
#     pass


def check_for_table(conn, tablename):
    return inspect(conn).has_table(tablename)


def run_alembic_upgrade(conn, cfg):
    command.upgrade(cfg, "head")


def run_alambic_stamp_head(conn, cfg):  
    command.stamp(cfg, "head")


async def init_db():
    # load config before for setting up loggin
    alembic_cfg = Config("./alembic.ini")

    from models import Base
    database_path = get_db_url()
    engine = create_async_engine(database_path)
    db_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        is_new_database = not (await conn.run_sync(check_for_table, "raid"))
        print("Create new database ? ", end="")
        alembic_cfg.attributes["connection"] = conn
        if is_new_database:
            print("yes")
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(run_alambic_stamp_head, alembic_cfg)

            add_functions = []  # [add_raids, add_items]
            for add_fn in add_functions:
                await add_fn(sess=db_session)
        else:
            print("no")
            await conn.run_sync(run_alembic_upgrade, alembic_cfg)

    return db_session, engine


