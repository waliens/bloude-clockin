import datetime
from discord import Embed, InvalidArgument
from db_util.attendance import record_attendance, record_batch_attendance

from db_util.wow_data import RaidSizeEnum
from ui.raid import RaidSelectView

from pycord18n.extension import _ as _t


class CharacterAttendanceEmbed(Embed):
  def __init__(self, character, attendances, datetime_range: tuple, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.title = _t("attendance.report.attendance_for", char_name=character.name)
    self.description = _t("attendance.report.for_raids_in", _from=datetime_range[0].strftime('%d/%m/%Y'), _to=datetime_range[1].strftime('%d/%m/%Y'))
    self._attendances = sorted(attendances, key=lambda a: a.raid_datetime)

    field_values = list()
    for attendance in self._attendances:
      desc = ""
      if attendance.in_dkp:
       desc += ":lock: " 
      desc += f"{attendance.raid_datetime.strftime('%d/%m/%Y %H:%M')}: {attendance.raid.short_name}{'10' if attendance.raid_size == RaidSizeEnum.RAID10 else '25'}"
      field_values.append(desc)

    field_value = "\n".join(field_values)
    if len(field_value) == 0:
      field_value = _t("general.no_data")
    self.add_field(name=_t("attendance.report.raids"), value=field_value)


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
        await record_attendance(sess, id_character=self._id_character, raid_datetime=self._raid_datetime, raid_size=RaidSizeEnum[size], id_raid=int(raid))

  def success_message(self):
    return {"content": _t("attendance.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("attendance.add.error", error=str(error)), "embed": None, "view": None}


class BatchAttendanceRaidSelectView(RaidSelectView):
  def __init__(self, bot, raids, characters: list, raid_datetime: datetime.datetime, guild_event=False, error_text: str="", *args, **kwargs) -> None:
    """
    characters: dict
      Index that maps identifier with Character model
    """
    super().__init__(bot, raids, *args, **kwargs)
    self._characters = {c.id: c for c in characters}
    self._raid_datetime = raid_datetime
    self._guild_event = guild_event
    self._error_text = error_text

  async def confirm_callback(self, *values):
    raids, sizes = values
    raid, size = raids[0], sizes[0]
    async with self.bot.db_session_class() as sess:
      async with sess.begin():
        errors = await record_batch_attendance(sess, 
          id_characters=[c.id for c in self._characters.values()],
          raid_datetime=self._raid_datetime,
          raid_size=RaidSizeEnum[size],
          id_raid=int(raid), 
          guild_event=self._guild_event)

        if len(errors) > 0 or len(self._error_text) > 0:
          final_error_txt = _t("attendance.invalid.partial_success")
          final_error_txt += f"\n{self._error_text}"
          for char_id, error in errors.items():
            final_error_txt += f"\n- {_t('attendance.invalid.for_character', char_name=self._characters[char_id].name, error=str(error))}"
          raise InvalidArgument(final_error_txt)

  def success_message(self):
    return {"content": _t("attendance.raid_helper.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("attendance.raid_helper.error", error=str(error)), "embed": None, "view": None}
  