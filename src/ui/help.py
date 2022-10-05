from discord import Cog, Embed, SlashCommandGroup, ApplicationContext
from discord.ext import commands

from pycord18n.extension import _ as _t


class CogToNameTwoWayIndex():
  def __init__(self):
    self._cog2name = {
      "AttendanceCog": "Attendance",
      "CharacterCog": "Character",
      "GuildInfoCog": "Charter",
      "HelloCog": "Hello",
      "HelpCog": "Help",
      "LootCog": "Loot",
      "RecipeCog": "Recipe",
      "SettingsCog": "Settings"
    }
    self._name2cog = {v: k for k, v in self._cog2name.items()}

  def get_cog(self, name: str, bot: commands.Bot):
    cog_class_name = self._name2cog.get(name)
    for class_name, cog in bot.cogs.items():
      if class_name == cog_class_name:
        return cog
    return None

  def get_name(self, cog: Cog):
    return self._cog2name.get(cog.__class__.__name__)


MAX_EMBED_LENGTH = 6000


class HelpEmbed(Embed):
  def __init__(self, ctx: ApplicationContext, *args, command_group: str, **kwargs):
    super().__init__(*args, **kwargs)
    index = CogToNameTwoWayIndex()
    cogs_for_help = ctx.bot.cogs.values()
    self.title = _t("help.full.title")
    if command_group is not None and index.get_cog(command_group, ctx.bot) is not None:
      cogs_for_help = [index.get_cog(command_group, ctx.bot)]
      self.title = _t("help.cog.title", group=command_group)
    self._fill_help(ctx, cogs_for_help)

  def _fill_help(self, ctx, cogs_for_help):
    total_length = 0
    too_long_msg = _t("help.invalid.toolong")
    
    for cog in cogs_for_help:
      for cmd in cog.walk_commands():
        if isinstance(cmd, SlashCommandGroup):
          continue
        if not all([check(ctx) for check in cmd.checks]):  # hide unavailable commands
          continue
      
        if cmd.is_subcommand:
          name = f"`/{cmd.full_parent_name.strip()} {cmd.name}`"
          key = f"help.{cmd.full_parent_name.strip()} {cmd.name}".replace(" ", ".")
        else:
          name = f"`/{cmd.name}`"
          key = f"help.{cmd.name}"

        option_key_prefix = f"{key}.option"

        options = list()
        for option in cmd.options:
          option_desc = f"{option.name}"
          if not option.required:
            option_desc = f"[{option_desc}]"

          option_key = f"{option_key_prefix}.{option.name}"
          option_desc = f"- `{option_desc}` {_t(option_key)}"
          options.append(option_desc)
          
        desc_key = f"{key}.desc"
        description = f"{_t(desc_key)}\n"
        description += "\n".join(options) 

        total_length += len(name) + len(description)
        if total_length > MAX_EMBED_LENGTH - len(too_long_msg):
          self.set_footer(text=too_long_msg)
          return

        self.add_field(name=name, value=description, inline=False)