

from discord import Guild, InvalidArgument
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from ui.guild_info import GuildCharter

async def get_guild_charter(sess, id_guild):
  """Get the charter of a guild"""
  try:
    query = select(GuildCharter).where(GuildCharter.id_guild == id_guild)
    results = await sess.execute(query)
    return results.unique().scalars().one()
  except NoResultFound as e:
    raise InvalidArgument("no charter for this guild")