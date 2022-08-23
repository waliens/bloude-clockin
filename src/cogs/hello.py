import discord
from discord.ext import commands
from pycord18n.extension import _ as _t

from models import GuildSettings


class Hello(commands.Cog): 
  def __init__(self, bot): 
    self.bot = bot

  @discord.slash_command()
  async def cheer(self, ctx):
    async with ctx.bot.db_session_class() as sess:
      async with sess.begin():
        settings = await sess.get(GuildSettings, str(ctx.guild.id))
        if settings is None or settings.cheer_message is None:
          message = _t("settings.cheer.default")
        else:
          message = settings.cheer_message
        await ctx.respond(message)

def setup(bot): # this is called by Pycord to setup the cog
  bot.add_cog(Hello(bot)) # add the cog to the bot