from discord.ext import commands


class AttendanceCog(commands.Cog):
  def __init__(self, bot) -> None:
    self._bot = bot


def setup(bot):
  bot.add_cog(AttendanceCog(bot))