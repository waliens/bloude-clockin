import discord
import enum
from discord.ext import commands
from discord import AutocompleteContext, Option, InvalidArgument
from ui.help import CogToNameTwoWayIndex, HelpEmbed

from pycord18n.extension import _ as _t


def get_active_cogs(ctx: AutocompleteContext):
  idx = CogToNameTwoWayIndex()
  return [idx.get_name(cog) for cog in ctx.bot.cogs.values()]


class CogsEnum(enum.Enum):
  PRESENCE = "Presence"
  CHARACTER = "Character"
  CHARTER = "Charter"
  HELLO = "Hello"
  HELP = "Help"
  LOOT = "Loot"
  RECIPE = "Recipe"
  SETTINGS = "Settings"


class HelpCog(commands.Cog): 
  def __init__(self, bot): 
    self.bot = bot

  @discord.slash_command()
  async def help(self, ctx, 
    command_group: Option(CogsEnum, description="Restrict the help to a command group.") = None, # , autocomplete=get_active_cogs
    public: Option(bool, description="display publicly") = False
  ):
    try:
      if command_group is not None:
        command_group = command_group.value
      embed = HelpEmbed(ctx, command_group=command_group)
      await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(_t("help.error", error=str(e)), ephemeral=True)


def setup(bot):
  bot.add_cog(HelpCog(bot))