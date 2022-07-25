import discord
from discord.ext import commands


class Hello(commands.Cog): 
  def __init__(self, bot): # this is a special method that is called when the cog is loaded
    self.bot = bot

  @discord.slash_command()
  async def hello(self, ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"Hello {name}!")
  
  @discord.slash_command() # create a slash command
  async def bb(self, ctx):
    await ctx.respond('Bloudiens, bloudiennes!')


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Hello(bot)) # add the cog to the bot