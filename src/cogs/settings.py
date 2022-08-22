from discord import guild_only, SlashCommandGroup, Option, InvalidArgument
from discord.ext import commands
from pycord18n.extension import _ as _t, I18nExtension
from models import GuildSettings


class SettingsCog(commands.Cog):
  def __init__(self, bot):
    self._bot = bot

  setting_group = SlashCommandGroup("settings", "Display, update and sign tracking of a guild setting.")
  
  @setting_group.command(description="Set/update locale")
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
            settings = GuildSettings(id_guild=guild_id, locale=locale, timezone=GuildSettings.DEFAULT_TZ)
            sess.add(settings)
          else:
            settings.locale = locale
          await sess.commit()

          # update locale
          I18nExtension.default_i18n_instance.set_current_locale(locale)
          await ctx.respond(_t("settings.locale.update.success", _locale=locale), ephemeral=True)
          
    except InvalidArgument as e:
      await ctx.respond(_t("settings.locale.update.error", error=str(e)), ephemeral=True)


def setup(bot):
  bot.add_cog(SettingsCog(bot))