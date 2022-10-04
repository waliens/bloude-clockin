import datetime
import re
import pytz
import discord
from discord import InvalidArgument, Option, guild_only, TextChannel, NotFound, Forbidden, HTTPException
from discord.ext import commands
from db_util.character import get_character
from db_util.attendance import fetch_attendances, record_batch_attendance
from db_util.raid import get_raids
from db_util.raid_helper import extract_raid_helpers_data
from ui.attendance import BatchAttendanceRaidSelectView, CharacterAttendanceEmbed, AttendanceRaidSelectView

from .util import get_applied_user_id, parse_date, parse_datetime

from pycord18n.extension import _ as _t


class AttendanceCog(commands.Cog):
  attendance_group = discord.SlashCommandGroup("attendance", "Attendance management")

  def __init__(self, bot) -> None:
    self.bot = bot

  @attendance_group.command(description="Indicate you have attended a raid")
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
          view = AttendanceRaidSelectView(self.bot, raids, character.id, raid_datetime)
          await ctx.respond(
            _t("attendance.add.locking_in", char_name=character.name, lock_at=raid_datetime.strftime('%d/%m/%Y %H:%M')), 
            view=view, 
            ephemeral=True
          )
    except InvalidArgument as e:
      await ctx.respond(_t("attendance.add.error", error=str(e)), ephemeral=True)

  @attendance_group.command(description="Register raid attendance from a RaidHelper.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def raid_helper(self, ctx,
    raid_helper_id: Option(str, description="The RaidHelper identifier")
  ):
    try:
      await ctx.defer(ephemeral=True)
      guild_id = str(ctx.guild.id)

      if re.match("^[0-9]+$", raid_helper_id) is None:
        raise InvalidArgument(_t("attendance.invalid.raid_helper_id"))

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          when, chars, missing = await extract_raid_helpers_data(sess, raid_helper_id, guild_id)
          raids = await get_raids(sess)
          error_txt = ""
          if len(missing) > 0:
            error_txt = "- " + _t("attendance.invalid.cannot_add_for_users", user_list=",".join(missing))
          view = BatchAttendanceRaidSelectView(ctx.bot, 
            raids=raids, 
            characters=chars, 
            raid_datetime=when, 
            guild_event=True, 
            error_text=error_txt)
          await ctx.respond(view=view)
    
    except InvalidArgument as e:
      await ctx.respond(_t("attendance.raid_helper.error", error=str(e)), ephemeral=True)


  @attendance_group.command(description="List the raids attended by a character")
  @guild_only()
  async def report(self, ctx,
    char_name: Option(str, name="character", description="Character name") = None,
    date_from: Option(str, name="from", description="Determine the first raid reset week to consider (format: DD/MM/YYYY). Default: 1 month back.") = None,
    date_to: Option(str, name="to", description="Determine the last raid reset week to consider (format: DD/MM/YYYY). Default: current reset.") = None,
    public: Option(bool, description="True: anyone can see the report, False: only the request inititator.") = False,
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
          await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(f"Cannot report the attendance: {str(e)}", ephemeral=True)


def setup(bot):
  bot.add_cog(AttendanceCog(bot))