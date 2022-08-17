import datetime
from discord.ui import View, Button
from discord import Interaction, InvalidArgument, SelectOption
from db_util.attendance import record_attendance
from ui.util import DeferSelect, EnumSelect
from db_util.wow_data import RaidSizeEnum

class RaidSelect(DeferSelect):
  def _item2option(self, item):
     return SelectOption(label=item.name, value=str(item.id))

  
class RaidSelectorModal(View):
  def __init__(self, bot, raids, id_character: int, raid_datetime: datetime.datetime, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self._id_character = id_character
    self._raid_datetime = raid_datetime
    self._bot = bot

    self._raid_selector = RaidSelect(raids)
    self._raid_size_selector = EnumSelect(RaidSizeEnum)
    self._button = Button(label="Confirm")

    async def button_callback(interaction: Interaction):

      try:
        async with self._bot.db_session_class() as sess:
          async with sess.begin():
            await record_attendance(
              sess, 
              id_character=self._id_character, 
              raid_datetime=self._raid_datetime, 
              raid_size=RaidSizeEnum[self._raid_size_selector.values[0]], 
              id_raid=int(self._raid_selector.values[0]))
            
        self.disable_all_items()
        self.stop()
        await interaction.response.send_message(f"The character is now locked in the selected raid.", ephemeral=True)
        
      except InvalidArgument as e:
        return await interaction.response.send_message(f"Cannot lock the character: {str(e)}.", ephemeral=True)

    self._button.callback = button_callback

    self.add_item(self._raid_selector)
    self.add_item(self._raid_size_selector)
    self.add_item(self._button)


  