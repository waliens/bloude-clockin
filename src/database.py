import json
import logging
import os
from dateutil.parser import isoparse
import pytz


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from alembic.config import Config
from alembic import command

from models import Item, Raid


def get_db_url():
  username = os.getenv("POSTGRES_USER")
  password = os.getenv("POSTGRES_PASSWORD")
  host = os.getenv("POSTGRES_HOST")
  dbname = os.getenv("POSTGRES_DB")
  return "postgresql+asyncpg://{}:{}@{}/{}".format(username, password, host, dbname)


async def add_raids(session):
  with open("./data/raids.json", "r", encoding="utf-8") as file:
    raids = [Raid(**{
        k: (isoparse(v).astimezone(pytz.UTC).replace(tzinfo=None) if k == "reset_start" else v) for k, v in raid.items()
    }) for raid in json.load(file)]
    logging.getLogger().info("Loading raids into the database.")
    session.add_all(raids)
    

async def add_items(session):
  with open("./data/items.json", "r", encoding="utf-8") as file:
    items = [Item(**item) for item in json.load(file)]
    logging.getLogger().info("Loading items into the database.")
    session.add_all(items)


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
        alembic_cfg.attributes["connection"] = conn
        if is_new_database:
            logging.getLogger().info("Create a new database.")
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(run_alambic_stamp_head, alembic_cfg)
            await conn.commit()
            
            add_functions = [add_raids, add_items]
            async with db_session() as sess:
                async with sess.begin():
                    for add_fn in add_functions:
                        await add_fn(sess)
                    await sess.commit()
        else:
            logging.getLogger().info("Check for database upgrade.")
            await conn.run_sync(run_alembic_upgrade, alembic_cfg)

    return db_session, engine


