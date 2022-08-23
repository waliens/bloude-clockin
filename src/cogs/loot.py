
from discord import InvalidArgument, Option
from discord.ext import commands
import discord

from cogs.util import get_applied_user_id
from db_util.character import get_character
from db_util.item import items_search
from ui.item import ItemListEmbed, LootListSelectorView

from pycord18n.extension import _ as _t

class LootCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @discord.slash_command(description="Report a loot you have obtained")
  async def loot(self, ctx,
    item_name: str = None,
    item_id: Option(int, name="id") = None,
    char_name: Option(str, name="character") = None,
    for_user: discord.Member = None
  ):
    """
    """
    try:
      if item_name is None and item_id is None:
        raise InvalidArgument(_t("loot.invalid.missinginfo"))
      if item_name is not None and item_id is not None:
        raise InvalidArgument(_t("loot.invalid.toomuchinfo"))
        
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          max_items = 10
          character = await get_character(sess, guild_id, user_id, char_name)
          items = await items_search(sess, item_name, item_id, max_items=max_items + 1)
          item_list_embed = ItemListEmbed(items, max_items=max_items, title=_t("loot.list.ui.matching"))
          item_list_selector_view = LootListSelectorView(self.bot, items, character.id, max_items=max_items)
          await ctx.respond(embed=item_list_embed, view=item_list_selector_view, ephemeral=True)

    except InvalidArgument as e:
      await ctx.respond(_t("loot.add.error", error=str(e)), ephemeral=True)


def setup(bot):
  bot.add_cog(LootCog(bot))