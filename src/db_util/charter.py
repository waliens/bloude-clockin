

from discord import InvalidArgument
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from pycord18n.extension import _ as _t

from ui.guild_info import GuildCharter


async def get_guild_charter(sess, id_guild: str):
  """Get the charter of a guild"""
  try:
    query = select(GuildCharter).where(GuildCharter.id_guild == id_guild)
    results = await sess.execute(query)
    return results.unique().scalars().one()
  except NoResultFound as e:
    raise InvalidArgument(_t("charter.invalid.none"))