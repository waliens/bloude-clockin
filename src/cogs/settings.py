from discord import guild_only, SlashCommandGroup, Option, InvalidArgument
from discord.ext import commands
from pycord18n.extension import _ as _t, I18nExtension
from db_util.gsheet_export import export_in_worksheets
from gsheet_helpers import SheetStateEnum, check_sheet, make_bot_guser_name
from models import GuildSettings


class SettingsCog(commands.Cog):
  def __init__(self, bot):
    self._bot = bot

  settings_group = SlashCommandGroup("settings", "Display, update and sign tracking of a guild setting.")
  gsheet_settings = settings_group.create_subgroup("gsheet", "Gsheet references management.")

  @staticmethod
  def _default_settings(guild_id):
    return GuildSettings(
      id_guild=guild_id, 
      locale=GuildSettings.DEFAULT_LOCALE, 
      timezone=GuildSettings.DEFAULT_TZ, 
      cheer_message=None,
      id_export_gsheet=None
    )

  @settings_group.command(description="Set/update locale")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def locale(self, ctx, 
    locale: Option(str, description="The locale string (e.g. 'en', 'fr').")
  ):
    try:
      guild_id = str(ctx.guild.id)
      if locale not in {"en", "fr"}:
        raise InvalidArgument(_t("settings.locale.invalid"))

      async with ctx.bot.db_session_class() as sess:
        async with sess.begin():
          settings = await sess.get(GuildSettings, guild_id)
          if settings is None:
            settings = SettingsCog._default_settings(guild_id)
            sess.add(settings)
          settings.locale = locale
          await sess.commit()

          # update locale
          I18nExtension.default_i18n_instance.set_current_locale(locale)
          await ctx.respond(_t("settings.locale.update.success", _locale=locale), ephemeral=True)
          
    except InvalidArgument as e:
      await ctx.respond(_t("settings.locale.update.error", error=str(e)), ephemeral=True)
  
  @settings_group.command(description="Set/update/remove the cheer message")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def cheer(self, ctx, 
    message: Option(str, description="A cheer message, leave empty for removal.") = None
  ):
    try:
      guild_id = str(ctx.guild.id)
      
      if message is not None:
        message = message.strip()
        if len(message) == 0:
          message == None
        elif len(message) > GuildSettings.cheer_message.type.length:
          raise InvalidArgument(_t("too long"))

      async with ctx.bot.db_session_class() as sess:
        async with sess.begin():
          settings = await sess.get(GuildSettings, guild_id)
          if settings is None:
            settings = SettingsCog._default_settings(guild_id)
            sess.add(settings)
          settings.cheer_message = message
          await sess.commit()

          await ctx.respond(_t("settings.cheer.update.success"), ephemeral=True)
          
    except InvalidArgument as e:
      await ctx.respond(_t("settings.cheer.update.error", error=str(e)), ephemeral=True)

  @gsheet_settings.command(description="Register the identifier of a spreadsheet to export.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def set(self, ctx,
    identifier: Option(str, description="The Google sheet identifier.") 
  ):
    try:
      guild_id = str(ctx.guild.id)

      check_status = check_sheet(identifier)
      if check_status == SheetStateEnum.UNKNOWN_SHEET:
        raise InvalidArgument(_t("settings.gsheet.notfound"))

      async with ctx.bot.db_session_class() as sess:
        async with sess.begin():
          settings = await sess.get(GuildSettings, guild_id)
          if settings is None:
            settings = SettingsCog._default_settings(guild_id)
            sess.add(settings)
          settings.id_export_gsheet = identifier
          await sess.commit()
          if check_status == SheetStateEnum.OK:
            await ctx.respond(_t("settings.gsheet.identifier.success"), ephemeral=True)
          else:
            await ctx.respond(_t("settings.gsheet.identifier.needs.perms", bot_gaccount=make_bot_guser_name()), ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("settings.gsheet.identifier.error", error=str(e)), ephemeral=True)

  @gsheet_settings.command(description="Displays the name of the bot Google account.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def account(self, ctx):
    await ctx.respond(_t("settings.gsheet.google.name", bot_gaccount=make_bot_guser_name()), ephemeral=True)

  @gsheet_settings.command(description="Trigger data export to the Google sheet.")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def export(self, ctx):
    try:
      async with ctx.bot.db_session_class() as sess:
        async with sess.begin():
          await ctx.defer(ephemeral=True)
          await export_in_worksheets(sess, str(ctx.guild.id))
          await ctx.respond(_t("settings.gsheet.export.success"), ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("settings.gsheet.export.error", error=str(e)), ephemeral=True)

def setup(bot):
  bot.add_cog(SettingsCog(bot))