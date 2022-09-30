import datetime
from discord import Embed, InvalidArgument
from db_util.attendance import record_attendance

from db_util.wow_data import RaidSizeEnum
from ui.raid import RaidSelectView

from pycord18n.extension import _ as _t


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


class AttendanceRaidSelectView(RaidSelectView):
  def __init__(self, bot, raids, id_character: int, raid_datetime: datetime.datetime, *args, **kwargs) -> None:
    super().__init__(bot, raids, *args, **kwargs)
    self._id_character = id_character
    self._raid_datetime = raid_datetime

  async def confirm_callback(self, *values):
    raids, sizes = values
    raid, size = raids[0], sizes[0]
    async with self.bot.db_session_class() as sess:
      async with sess.begin():
        await record_attendance(sess, id_character=self._id_character, raid_datetime=self._raid_datetime, raid_size=RaidSizeEnum[raid], id_raid=int(size))

  def success_message(self):
    return {"content": _t("attendance.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("attendance.add.error", error=str(error)), "embed": None, "view": None}