import logging
import os
from discord.ext import commands
from database import init_db

class BloudeClockInBot(commands.Bot):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    cog_exts = [
      "hello", 
      "character",
      "attendance",
      "loot",
      "guild_info"
    ]

    for cog_ext in cog_exts:
      cog_full_ext = f"cogs.{cog_ext}"
      result = self.load_extension(cog_full_ext)
      if isinstance(result[cog_full_ext], bool):
        logging.getLogger().info("loading '{}': successful".format(cog_full_ext))
      else:
        logging.getLogger().error("loading '{}': {}".format(cog_full_ext, str(result[cog_full_ext])))
        
    self._db_session = None
    self._db_engine = None

  @property
  def db_session(self):
    return self._db_session

  @property
  def db_engine(self):
    return self._db_engine
  
  async def on_ready(self):
    logging.getLogger().info("Bot `{}` is ready.".format(self.bot_classname))

  async def on_connect(self):
    await self._connect_db()
    logging.getLogger().info("Bot `{}` is connected.".format(self.bot_classname))

  async def on_disconnect(self):
    # await self._disconnect_db()
    logging.getLogger().info("Bot `{}` is disconnected.".format(self.bot_classname))

  async def on_resume(self):
    await self._connect_db()
    logging.getLogger().info("Bot `{}` resumed.".format(self.bot_classname))

  async def _disconnect_db(self):
    await self._do_disconnect_db()
    logging.getLogger().info("Bot `{}` disconnected from the database.".format(self.bot_classname))

  async def _do_disconnect_db(self):
    if self._db_engine is not None:
      await self._db_engine.dispose()

    self._db_engine = None
    self._db_session = None

  async def _connect_db(self):
    await self._do_disconnect_db()
    self._db_session, self._db_engine = await init_db()
    logging.getLogger().info("Bot `{}` successfully connected to the database.".format(self.bot_classname))

  @property
  def bot_classname(self):
    return self.__class__.__name__
