import json
import logging
import os
from dateutil.parser import isoparse
import pytz

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from alembic.config import Config
from alembic import command

from db_util.wow_data import ProfessionEnum


def get_db_url(with_async=True):
  username = os.getenv("POSTGRES_USER")
  password = os.getenv("POSTGRES_PASSWORD")
  host = os.getenv("POSTGRES_HOST")
  dbname = os.getenv("POSTGRES_DB")
  port = os.getenv("POSTGRES_PORT", "5432")
  driver = "asyncpg" if with_async else "psycopg2"
  return "postgresql+{}://{}:{}@{}:{}/{}".format(driver, username, password, host, port, dbname)


async def add_raids(session):
  from models import Raid
  with open("./data/raids.json", "r", encoding="utf-8") as file:
    raids = [Raid(**{
        k: (isoparse(v).astimezone(pytz.UTC).replace(tzinfo=None) if k == "reset_start" else v) for k, v in raid.items()
    }) for raid in json.load(file)]
    logging.getLogger().info("Loading raids into the database.")
    session.add_all(raids)
    

async def add_items(session):
  from models import Item
  with open("./data/items.json", "r", encoding="utf-8") as file:
    items = [Item(**item) for item in json.load(file)]
    logging.getLogger().info("Loading items into the database.")
    session.add_all(items)



async def add_recipes(session):
  from models import Recipe
  with open("./data/recipes.json", "r", encoding="utf-8") as file:
    recipes = list()
    for recipe in json.load(file):
        recipe_model = Recipe(**recipe)
        recipe_model.profession = ProfessionEnum[recipe["profession"]]
        recipes.append(recipe_model)
    logging.getLogger().info("Loading recipes into the database.")
    session.add_all(recipes)



async def add_charters(session):
  from models import GuildCharter, GuildCharterField
  with open("./data/charters.json", "r", encoding="utf-8") as file:
    for guild in json.load(file):
        charter = GuildCharter(**{k:v for k, v in guild.items() if k != "fields"})
        charter_fields = [GuildCharterField(id_guild=guild["id_guild"], **field) for field in guild["fields"]]
        session.add(charter)
        session.add_all(charter_fields) 


def check_for_table(conn, tablename):
    return inspect(conn).has_table(tablename)


def run_alembic_upgrade(conn, cfg):
    command.upgrade(cfg, "head")


def run_alambic_stamp_head(conn, cfg):  
    command.stamp(cfg, "head")


async def init_db():
    # load config before for setting up loggin
    alembic_cfg = Config("./alembic.ini")

    versions_folder = "./alembic/versions"
    if not os.path.exists(versions_folder):
        os.makedirs(versions_folder)

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
            
            add_functions = [add_raids, add_items, add_charters, add_recipes]
            async with db_session() as sess:
                async with sess.begin():
                    for add_fn in add_functions:
                        await add_fn(sess)
                    await sess.commit()
        else:
            logging.getLogger().info("Check for database upgrade.")
            await conn.run_sync(run_alembic_upgrade, alembic_cfg)

    return db_session, engine


