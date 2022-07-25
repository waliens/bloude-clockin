import logging
from discord import slash_command, user_command
from discord.ext import commands
from database import init_db

class BloudeClockInBot(commands.Bot):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)

    cog_exts = ["hello"] 
    for cog_ext in cog_exts:
      self.load_extension("cogs.{}".format(cog_ext))

    self._db_session = None
    self._db_engine = None
  
  async def on_ready(self):
    self._db_session, self._db_engine = await init_db()
    logging.getLogger().info("Bot `{}` is running.".format(self.__class__))
