
from os import remove
from pydoc import describe
import re
from discord import InvalidArgument, Option, SlashCommandGroup
from discord.ext import commands
import discord

from cogs.util import get_applied_user_id, parse_loots_str
from db_util.character import get_character
from db_util.item import fetch_loots, items_search, register_bulk_loots, remove_loots
from db_util.wow_data import InventorySlotEnum
from models import Loot
from ui.item import ItemListEmbed, LootListEmbed, LootListSelectorView

from pycord18n.extension import _ as _t


class LootCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  loot_group = SlashCommandGroup("loot", "A command group for managing loots")

  @loot_group.command(description="Register a loot you have obtained")
  async def register(self, ctx,
    item_name: str = None,
    item_id: Option(int, name="id") = None,
    char_name: Option(str, name="character") = None,
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None
  ):
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
          item_list_embed = ItemListEmbed(items, max_items=max_items, title=_t("general.ui.list.matching"))
          item_list_selector_view = LootListSelectorView(self.bot, items, character.id, max_items=max_items)
          await ctx.respond(embed=item_list_embed, view=item_list_selector_view, ephemeral=True)

    except InvalidArgument as e:
      await ctx.respond(_t("loot.add.error", error=str(e)), ephemeral=True)


  @loot_group.command(description="Remove one item from your loot list")
  async def remove(self, ctx,
    item_id: Option(int, name="id"),
    remove_all: Option(bool, name="all", description="True to remove all occurences of this item, instead of just one") = False, 
    char_name: Option(str, name="character") = None,
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None
  ):
    try:
      await ctx.defer(ephemeral=True)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          character = await get_character(sess, guild_id, user_id, char_name)
          await remove_loots(sess, character.id, item_id, only_last=not remove_all, force_remove_in_dkp=False)  # users cannot remove loots in_dkp
          await ctx.respond(_t("loot.delete.success"), ephemeral=True) 

    except InvalidArgument as e:
      await ctx.respond(_t("loot.delete.error", error=str(e)), ephemeral=True)

  @loot_group.command(description="Add loot in bulks. By default they are added to the dkp system.")
  @commands.has_permissions(administrator=True)
  async def bulk(self, ctx, 
    loots: Option(str, description="List of player names and item identifiers. Example: ´Arthas:40800,39865;Lutherqt:25006´."),
    in_dkp: Option(str, description="Whether or not these loots should be included in dkp system (True by default).") = True
  ):
    try:
      guild_id = str(ctx.guild_id)
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          await register_bulk_loots(sess, guild_id, parse_loots_str(loots), in_dkp=in_dkp)
          await ctx.respond(_t("loot.bulk.success"), ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("loot.bulk.error", error=str(e)), ephemeral=True)

  @discord.slash_command(description="List loots for a character.")
  async def loots(self, ctx,
    slot: Option(InventorySlotEnum, description="An inventory slot") = None,
    char_name: Option(str, name="character") = None,
    for_user: Option(discord.Member) = None,
    show_ids: Option(bool) = False
  ):
    try:
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          max_items = 50
          character = await get_character(sess, guild_id, user_id, char_name)
          loots = await fetch_loots(sess, character.id, slot=slot, max_items=max_items + 1)
          item_list_embed = LootListEmbed(loots, max_items=max_items, show_ids=show_ids, title=_t("loot.list.ui.loots"))
          await ctx.respond(embed=item_list_embed, ephemeral=True)

    except InvalidArgument as e:
      await ctx.respond(_t("loot.list.error", error=str(e)), ephemeral=True)

def setup(bot):
  bot.add_cog(LootCog(bot))