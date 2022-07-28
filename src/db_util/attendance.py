from cgitb import reset
import re
import pytz
import datetime

from sqlalchemy.exc import NoResultFound
from sqlalchemy import select
from models import Attendance, Raid
from discord import InvalidArgument
from db_util.wow_data import RaidSizeEnum


def get_reset_for_datetime(when: datetime.datetime, first_reset_start: datetime.datetime, first_reset_end: datetime.datetime, reset_period: int):
  """Computes the start and end datetimes of a raid reset a when datetime falls in, based on the first reset start and end date times and reset period.
  """
  delta = when - first_reset_start
  number_of_resets = delta.days // reset_period
  diff = datetime.timedelta(days=number_of_resets * reset_period)
  return first_reset_start + diff, first_reset_end + diff

  
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
    this_reset_start, this_reset_end = get_reset_for_datetime(raid_datetime, raid.reset_start, raid.first_reset_end, raid.reset_period)

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


async def fetch_attendances(session, id_character: int, date_from: datetime.date, date_to: datetime.date):
  """
  """

  datetime_from = datetime.datetime.combine(date_from, datetime.datetime.min.time())
  datetime_to = datetime.datetime.combine(date_to, datetime.datetime.max.time())
  
  # reset period is at most 7 days
  # events not in "from > to" range will be filtered afterwards (as we dont have the reset times info yet)
  query = select(Attendance).where(
    Attendance.id_character == id_character,
    Attendance.raid_datetime >= (datetime_from - datetime.timedelta(days=7)),
    Attendance.raid_datetime <= (datetime_to + datetime.timedelta(days=7))
  )

  query_results = await session.execute(query)

  # filter events out of the range
  resets_from_to_cache = dict() # maps (raid id, raid size) with exact (from, to) tuple
  valid_attendances = list()
  for attendance in query_results.scalars().all():
    # update from to cache if needed
    raid_key = (attendance.id_raid, attendance.raid_size)
    if raid_key not in resets_from_to_cache:
      r_start, r_end, r_period =  attendance.raid.reset_start, attendance.raid.first_reset_end, attendance.raid.reset_period
      from_for_raid, _ = get_reset_for_datetime(datetime_from, r_start, r_end, r_period)
      _, to_for_raid = get_reset_for_datetime(datetime_to, r_start, r_end, r_period)
      resets_from_to_cache[raid_key] = (from_for_raid, to_for_raid)
    
    # check if current attendance should be considered
    from_for_raid, to_for_raid = resets_from_to_cache[raid_key]
    if not (from_for_raid <= attendance.raid_datetime <= to_for_raid):
      continue

    valid_attendances.append(attendance)

  if len(resets_from_to_cache) > 0:
    actual_datetime_from = min([_from for _from, _ in resets_from_to_cache.values()])
    actual_datetime_to = max([_to for _, _to in resets_from_to_cache.values()])
  else:
    actual_datetime_from, actual_datetime_to = datetime_from, datetime_to

  return valid_attendances, (actual_datetime_from, actual_datetime_to)
