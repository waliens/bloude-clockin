from discord.ext import commands


class Hello(commands.Cog): 
  def __init__(self, bot): # this is a special method that is called when the cog is loaded
    self.bot = bot

  @commands.command()
  async def hello(self, ctx, name: str = None):
    name = name or ctx.author.name
    await ctx.respond(f"Hello {name}!")
  

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Hello(bot)) # add the cog to the bot