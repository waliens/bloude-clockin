import unittest
from discord.commands import SlashCommandGroup
from gci import GuildClockInBot

from lang.util import build_i18n

from pycord18n.extension import _ as _t

class HelpTest(unittest.TestCase):
  def setUp(self):
    self._i18n = build_i18n("./src/lang")
    self._bot = GuildClockInBot()

  def testHelpLanguageStringsPresence(self):
    for cog in self._bot.cogs.values():
      for cmd in cog.walk_commands():
        if isinstance(cmd, SlashCommandGroup):
          continue

        if cmd.is_subcommand:
          key = f"help.{cmd.full_parent_name.strip()} {cmd.name}".replace(" ", ".")
        else:
          key = f"help.{cmd.name}"

        option_key_prefix = f"{key}.option"

        for option in cmd.options:
          option_key = f"{option_key_prefix}.{option.name}"
          self.assertGreater(len(_t(option_key)), 0)
        
        desc_key = f"{key}.desc"
        self.assertGreater(len(_t(desc_key)), 0)

