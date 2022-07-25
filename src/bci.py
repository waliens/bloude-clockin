import logging
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
    

  @commands.slash_command() # create a slash command
  async def bb(self, ctx):
    await ctx.respond('Bloudiens, bloudiennes!')

  @commands.user_command(name="Say Hello")
  async def hi(self, ctx, user):
    await ctx.respond(f"{ctx.author.mention} says hello to {user.name}!")
