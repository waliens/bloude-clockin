import logging
from discord.ext import commands
from database import init_db

class BloudeClockInBot(commands.Bot):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    cog_exts = [
      "hello", 
      "character"
    ]

    for cog_ext in cog_exts:
      self.load_extension("cogs.{}".format(cog_ext))

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
    self._db_session, self._db_engine = await init_db()
    logging.getLogger().info("Bot `{}` successfully connected to the database.".format(self.bot_classname))
    logging.getLogger().info("Bot `{}` is connected.".format(self.bot_classname))

  async def on_disconnect(self):
    self._db_engine.dispose()
    self._db_engine = None
    self._db_session = None
    logging.getLogger().info("Bot `{}` disconnected from the database.".format(self.bot_classname))
    logging.getLogger().info("Bot `{}` is disconnected.".format(self.bot_classname))

  @property
  def bot_classname(self):
    return self.__class__.__name__
