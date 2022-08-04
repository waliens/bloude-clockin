


import select
from discord import Bot, Guild, InvalidArgument, Option, guild_only, slash_command
from discord.ext import commands
from db_util.charter import get_guild_charter
from models import GuildCharter

from ui.guild_info import GuildCharterEmbed


class GuildInfoCog(commands.Cog):
  def __init__(self, bot):
      self.bot = bot
      
  @slash_command(description="Charte de guilde")
  @guild_only()
  async def charter(self, ctx, 
    section: Option(int, description="A section number of the charter") = None, 
    show: Option(bool, description="To show the bot response and the charter publicly") = False, 
    official: Option(bool, description="To make this charter message the one that has to be signed. Removes the old charter if any.") =False):
    try:
      guild_id = str(ctx.guild.id)
      if (show or official) and not ctx.author.guild_permissions.administrator:
        raise InvalidArgument("cannot use this command without admin role")

      async with self.bot.db_session() as sess:
        async with sess.begin():
          charter = await get_guild_charter(sess, guild_id)
          embed = GuildCharterEmbed(charter, section=section)
          await ctx.respond(embed=embed, ephemeral=not show)
    except InvalidArgument as e:
      await ctx.respond(f"Cannot display rules: {str(e)}")


def setup(bot: Bot):
  bot.add_cog(GuildInfoCog(bot))