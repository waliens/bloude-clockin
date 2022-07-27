import datetime
import pytz
import logging
import discord
from discord import InvalidArgument, Option, SelectMenu, guild_only
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from db_util.character import get_character
from db_util.raid import get_raids
from models import Character
from ui.raid import RaidSelectorModal

from .util import get_applied_user_id, parse_datetime


class AttendanceCog(commands.Cog):
  def __init__(self, bot) -> None:
    self.bot = bot

  @discord.slash_command()
  @guild_only()
  async def presence(self, ctx,
    char_name: Option(str, name="character") = None, 
    raid_datetime: Option(str, name="when", description="DD/MM/YYYY HH:mm") = None,
    for_user: discord.Member = None,
  ):
    try:
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      raid_datetime = parse_datetime(raid_datetime, default=datetime.datetime.now(tz=pytz.UTC)).replace(tzinfo=None)

      async with self.bot.db_session() as sess:
        async with sess.begin():
          character = await get_character(sess, guild_id, user_id, name=char_name)
          raids = await get_raids(sess)
          await ctx.respond(
            f"Lock character '{character.name}' ({raid_datetime.strftime('%d/%m/%Y %H:%M')}) in:", 
            view=RaidSelectorModal(self.bot, raids, character.id, raid_datetime), ephemeral=True)

    except InvalidArgument as e:
      await ctx.respond(f"Cannot submit a presence: {str(e)}", ephemeral=True)


def setup(bot):
  bot.add_cog(AttendanceCog(bot))