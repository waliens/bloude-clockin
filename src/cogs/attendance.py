import datetime
import pytz
import logging
import discord
from discord import InvalidArgument, Option, SelectMenu, guild_only
from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from db_util.attendance import fetch_attendances
from db_util.character import get_character
from db_util.raid import get_raids
from models import Character
from ui.attendance import CharacterAttendanceEmbed
from ui.raid import RaidSelectorModal

from .util import get_applied_user_id, parse_date, parse_datetime


class AttendanceCog(commands.Cog):
  
  presence_group = discord.SlashCommandGroup("presence", "Presence management")

  def __init__(self, bot) -> None:
    self.bot = bot

  @presence_group.command(description="Indicate you have attended a raid")
  @guild_only()
  async def add(self, ctx,
    char_name: Option(str, name="character") = None, 
    raid_datetime: Option(str, name="when", description="DD/MM/YYYY HH:mm") = None,
    for_user: discord.Member = None,
  ):
    try:
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      raid_datetime = parse_datetime(raid_datetime, default=datetime.datetime.now(tz=pytz.UTC)).replace(tzinfo=None)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          character = await get_character(sess, guild_id, user_id, name=char_name)
          raids = await get_raids(sess)
          await ctx.respond(
            f"Lock character '{character.name}' ({raid_datetime.strftime('%d/%m/%Y %H:%M')}) in:", 
            view=RaidSelectorModal(self.bot, raids, character.id, raid_datetime), ephemeral=True)

    except InvalidArgument as e:
      await ctx.respond(f"Cannot submit a presence: {str(e)}", ephemeral=True)

  @presence_group.command(description="List the raids attended by a character")
  @guild_only()
  async def report(self, ctx,
    char_name: Option(str, name="character", description="Character name") = None,
    date_from: Option(str, name="from", description="Determine the first raid reset week to consider (format: DD/MM/YYYY). Default: 1 month back.") = None,
    date_to: Option(str, name="to", description="Determine the last raid reset week to consider (format: DD/MM/YYYY). Default: current reset.") = None,
    show: Option(bool, description="True: anyone can see the report, False: only the request inititator.") = False,
    for_user: discord.Member = None
  ):
    try:
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      date_from = parse_date(date_from, default=datetime.date.today())
      date_to = parse_date(date_to, default=datetime.date.today())

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          character = await get_character(sess, guild_id, user_id, char_name)
          attendances, actual_datetime_range = await fetch_attendances(sess, character.id, date_from, date_to)

          embed = CharacterAttendanceEmbed(character, attendances, actual_datetime_range)
          await ctx.respond(embed=embed, ephemeral=not show)
      
    except InvalidArgument as e:
      await ctx.respond(f"Cannot report the attendance: {str(e)}", ephemeral=True)
 


def setup(bot):
  bot.add_cog(AttendanceCog(bot))