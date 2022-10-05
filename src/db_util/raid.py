import pytz
import datetime
from sqlalchemy import select
from discord import InvalidArgument
from models import Raid

from pycord18n.extension import _ as _t

async def get_raids(session, active_only=False):
  query = select(Raid)
  if active_only:
    query = query.where(Raid.reset_start <= datetime.datetime.utcnow())
  results = await session.execute(query)
  return results.scalars().all()


async def update_raid_reset(sess, id_raid, reset: datetime.datetime):
  raid = await sess.get(Raid, id_raid)
  if raid is None:
    raise InvalidArgument(_t("raid.reset.update.notfound"))
  raid.reset_start = reset.astimezone(pytz.UTC).replace(tzinfo=None)
  await sess.commit()


  