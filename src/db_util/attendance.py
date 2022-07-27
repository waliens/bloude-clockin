import pytz
import datetime

from sqlalchemy.exc import NoResultFound
from sqlalchemy import select
from models import Attendance, Raid
from discord import InvalidArgument
from db_util.wow_data import RaidSizeEnum


def diff_in_weeks(d1: datetime.datetime, d2: datetime.datetime):
  monday1 = (d1 - datetime.timedelta(days=d1.weekday()))
  monday2 = (d2 - datetime.timedelta(days=d2.weekday()))
  return (monday2 - monday1).days // 7


async def record_attendance(session, id_character: int, raid_datetime: datetime.datetime, raid_size: RaidSizeEnum, id_raid: int):
  """
  Parameters
  ----------
  session: AsyncSession
    Database session
  character: int
    The character identifier
  raid_date: date
    The date of the raid
  raid_size: RaidSizeEnum
    size of the raid
  id_raid: int
    The raid identifier
  
  Returns
  -------

  """
  try:
    raid = (await session.execute(select(Raid).where(Raid.id == id_raid))).scalars().one()
    
    if raid_datetime < raid.reset_start:
      raise InvalidArgument("the given date is before the start of the expansion")

    # check if character has already recorded an attendance
    start, end = raid.reset_start, raid.first_reset_end
    weeks_delta = datetime.timedelta(weeks=diff_in_weeks(start, raid_datetime)) 
    this_reset_start, this_reset_end = start + weeks_delta, end + weeks_delta

    check_query = select(Attendance).where(
      Attendance.id_character == id_character,
      Attendance.id_raid == id_raid,
      Attendance.raid_size == raid_size,
      Attendance.raid_datetime < this_reset_end,
      Attendance.raid_datetime >= this_reset_start
    )

    attendance_count = len((await session.execute(check_query)).scalars().all())

    if attendance_count > 0:
      raise InvalidArgument(f"this character is already locked for this raid and raid size for the current reset ({this_reset_start} > {this_reset_end})")
    
    # add new attendance
    new_attendance = Attendance(
      id_character=id_character,
      id_raid=id_raid,
      raid_size=raid_size,
      raid_datetime=raid_datetime,
      cancelled=False,
      created_at=datetime.datetime.now(tz=pytz.UTC).replace(tzinfo=None)
    )

    session.add(new_attendance)
    await session.commit()

  except NoResultFound as e:
    raise InvalidArgument("unknown raid identifier")