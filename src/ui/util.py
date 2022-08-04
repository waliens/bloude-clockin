

from abc import abstractmethod
from discord.ui import Button, Select
from discord import ButtonStyle, Interaction, SelectOption


class DeferSelect(Select):
  def __init__(self, data, *args, **kwargs):
    super().__init__(
      options=[self._item2option(item) for item in data],
      *args, **kwargs
    )

  @abstractmethod
  def _item2option(self, item):
    pass

  async def callback(self, interaction: Interaction):
    return await interaction.response.defer(ephemeral=True)


class EnumSelect(DeferSelect):
  def _item2option(self, item):
    return SelectOption(label=item.name_hr, value=item.name)


class CancelButton(Button):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, style=ButtonStyle.danger, label="Cancel", **kwargs)

  async def callback(self, interaction: Interaction):
    return await interaction.response.edit_message(content="Cancelled.", view=None, embed=None)



