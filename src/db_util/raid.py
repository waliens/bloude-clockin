from sqlalchemy import select
from models import Raid

async def get_raids(session):
  return (await session.execute(select(Raid))).scalars().all()