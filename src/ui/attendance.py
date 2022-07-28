import datetime
from discord import Embed

from db_util.wow_data import RaidSizeEnum


# TODO group attendances by synchronized resets

class CharacterAttendanceEmbed(Embed):
  def __init__(self, character, attendances, datetime_range: tuple, *args, **kwargs):
    super().__init__(
      *args, 
      title=f"Attendance for {character.name}", 
      description=f"For raids from {datetime_range[0].strftime('%d/%m/%Y')} to {datetime_range[1].strftime('%d/%m/%Y')}.", 
      **kwargs)

    self._attendances = sorted(attendances, key=lambda a: a.raid_datetime)
    self.add_field(name="Raids", value="\n".join([
      f"{attendance.raid_datetime.strftime('%d/%m/%Y %H:%M')}: {attendance.raid.short_name}{'10' if attendance.raid_size == RaidSizeEnum.RAID10 else '25'}" 
      for attendance in self._attendances
    ]))