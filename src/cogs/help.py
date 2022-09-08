import discord
from discord.ext import commands
from discord import AutocompleteContext, Option, InvalidArgument
from ui.help import CogToNameTwoWayIndex, HelpEmbed

from pycord18n.extension import _ as _t


def get_active_cogs(ctx: AutocompleteContext):
  idx = CogToNameTwoWayIndex()
  return [idx.get_name(cog) for cog in ctx.bot.cogs.values()]


class HelpCog(commands.Cog): 
  def __init__(self, bot): 
    self.bot = bot

  @discord.slash_command()
  async def help(self, ctx, 
    #command_group: Option(str, description="Restrict the help to a command group.", autocomplete=get_active_cogs) = None,
    public: Option(bool, description="display publicly") = False
  ):
    try:
      embed = HelpEmbed(self.bot, command_group=None)
      await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(_t("help.error", error=str(e)), ephemeral=True)


def setup(bot):
  bot.add_cog(HelpCog(bot))