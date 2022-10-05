import datetime
from discord import SelectOption, InvalidArgument
from ui.util import DeferSelect, EnumSelect, MultiSelectView
from db_util.wow_data import RaidSizeEnum
from db_util.raid import update_raid_open_at
from lang.util import localized_attr

from pycord18n.extension import _ as _t


class RaidSelect(DeferSelect):
  def _item2option(self, item):
    return SelectOption(label=localized_attr(item, "name"), value=str(item.id))


class RaidSelectView(MultiSelectView):
  def __init__(self, bot, raids, *args, **kwargs):
    self._raid_select = RaidSelect(raids)
    self._size_select = EnumSelect(RaidSizeEnum)
    super().__init__(bot, [self._raid_select, self._size_select], *args, **kwargs)


class OpenAtUpdateRaidSelectView(MultiSelectView):
  def __init__(self, bot, raids, open_at_datetime: datetime.datetime, *args, **kwargs):
    self._raid_select = RaidSelect(raids)
    super().__init__(bot, [self._raid_select], *args, **kwargs)
    self._open_at_datetime = open_at_datetime
  
  async def confirm_callback(self, *values):
    raid_id = int(values[0][0])
    async with self.bot.db_session_class() as sess:
      async with sess.begin():
        await update_raid_open_at(sess, id_raid=raid_id, open_at=self._open_at_datetime)

  def success_message(self):
    return {"content": _t("raid.open.update.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("raid.open.update.error", error=str(error)), "embed": None, "view": None}