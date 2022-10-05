import pytz
import datetime

from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, func
from models import Attendance, Raid
from discord import InvalidArgument
from db_util.wow_data import RaidSizeEnum

from pycord18n.extension import _ as _t


class MultiInvalidArgument(InvalidArgument):
  def __init__(self, *invalid_arguments) -> None:
    super().__init__("\n".join([str(e) for e in invalid_arguments]))


def get_reset_for_datetime(when: datetime.datetime, first_reset_start: datetime.datetime, first_reset_end: datetime.datetime, reset_period: int):
  """Computes the start and end datetimes of a raid reset a when datetime falls in, based on the first reset start and end date times and reset period.
  """
  delta = when - first_reset_start
  number_of_resets = delta.days // reset_period
  diff = datetime.timedelta(days=number_of_resets * reset_period)
  return first_reset_start + diff, first_reset_end + diff


async def add_or_update_attendance(sess, 
  id_character: int, 
  raid_datetime: datetime.datetime, 
  raid: Raid, 
  raid_size: RaidSizeEnum,
  guild_event=False
):
  # check if character has already recorded an attendance
  this_reset_start, this_reset_end = get_reset_for_datetime(raid_datetime, raid.reset_start, raid.first_reset_end, raid.reset_period)

  check_query = select(Attendance).where(
    Attendance.id_character == id_character,
    Attendance.id_raid == raid.id,
    Attendance.raid_size == raid_size,
    Attendance.raid_datetime < this_reset_end,
    Attendance.raid_datetime >= this_reset_start
  )
  check_result = await sess.execute(check_query)
  attendance = check_result.scalars().one_or_none()

  if attendance is None:
    new_attendance = Attendance(
      id_character=id_character,
      id_raid=raid.id,
      is_guild_event=guild_event,
      raid_size=raid_size,
      raid_datetime=raid_datetime,
      cancelled=False,
      created_at=datetime.datetime.now(tz=pytz.UTC).replace(tzinfo=None)
    )

    sess.add(new_attendance)
  else:
    if not guild_event:
      raise InvalidArgument(_t("attendance.invalid.already_locked", reset_start=this_reset_start, reset_end=this_reset_end))
    if guild_event and not attendance.is_guild_event: # update to a guild event if not yet
      attendance.is_guild_event = guild_event
      attendance.raid_datetime = raid_datetime


  
async def record_attendance(session, id_character: int, raid_datetime: datetime.datetime, raid_size: RaidSizeEnum, id_raid: int, do_commit=True):
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
  do_commit: bool
    To commit the transaction
  Returns
  -------

  """
  try:
    raid = (await session.execute(select(Raid).where(Raid.id == id_raid))).scalars().one()
    
    if raid_datetime < raid.open_at:
      raise InvalidArgument(_t("attendance.invalid.raid_opens_later"))

    await add_or_update_attendance(
      sess=session, 
      id_character=id_character, 
      raid_datetime=raid_datetime,
      raid=raid,
      raid_size=raid_size,
      guild_event=False)

    if do_commit:
      await session.commit()

  except NoResultFound as e:
    raise InvalidArgument(_t("attendance.invalid.unknown_raid"))


async def record_batch_attendance(sess, id_characters, raid_datetime: datetime.datetime, raid_size: RaidSizeEnum, id_raid: int, guild_event=True, do_commit=True):
  """Returns a dictionnary of  
  """
  try:
    raid = (await sess.execute(select(Raid).where(Raid.id == id_raid))).scalars().one()
    
    if raid_datetime < raid.open_at:
      raise InvalidArgument(_t("attendance.invalid.raid_opens_later"))

    not_added = dict()
    for id_character in id_characters:
      try: 
        await add_or_update_attendance(sess, 
          id_character=id_character, 
          raid_datetime=raid_datetime, 
          raid=raid, 
          raid_size=raid_size, 
          guild_event=guild_event)
      except InvalidArgument as e:
        not_added[id_character] = e        
    
    if do_commit:
      await sess.commit()

    return not_added

  except NoResultFound as e:
    raise InvalidArgument(_t("attendance.invalid.unknown_raid"))


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

