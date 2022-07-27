import discord
from discord.ext import commands


class Hello(commands.Cog): 
  def __init__(self, bot): 
    self.bot = bot

  @discord.slash_command()
  async def bb(self, ctx):
    await ctx.respond('Bloudiens, bloudiennes!')


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Hello(bot)) # add the cog to the bot