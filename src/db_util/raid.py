import pytz
import datetime
from sqlalchemy import select
from discord import InvalidArgument
from models import Raid

from pycord18n.extension import _ as _t

async def get_raids(session, open_only=False):
  query = select(Raid)
  if open_only:
    query = query.where(Raid.open_at <= datetime.datetime.utcnow())
  results = await session.execute(query)
  return results.scalars().all()


async def update_raid_open_at(sess, id_raid, open_at: datetime.datetime):
  raid = await sess.get(Raid, id_raid)
  if raid is None:
    raise InvalidArgument(_t("raid.open.update.notfound"))
  raid.open_at = open_at.astimezone(pytz.UTC).replace(tzinfo=None)
  await sess.commit()

