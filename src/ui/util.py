

from abc import abstractmethod
from discord.ui import Button, Select, Modal, InputText
from discord import ButtonStyle, InputTextStyle, Interaction, InvalidArgument, SelectOption, Embed

from pycord18n.extension import _ as _t


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
    super().__init__(*args, style=ButtonStyle.danger, label=_t("general.cancel"), **kwargs)

  async def callback(self, interaction: Interaction):
    return await interaction.response.edit_message(content=_t("general.cancelled"), view=None, embed=None)



class EmbedFieldEditorModal(Modal):
  def __init__(self, 
    submit_callback, *args, 
    title_field_name="Title", 
    title_field_value="",
    min_title_size=1,
    max_title_size=256,
    content_field_name="Content", 
    content_field_value="",
    min_content_size=1, 
    max_content_size=1000, **kwargs
  ) -> None:
    """
    Parameters
    ----------
    submit_callback: async callback
      Handles modal submission and sends a response to the interaction, fn(interaction, title, content)
    title_field_name: str
    title_field_value: str
    content_field_name: str
    content_field_value: str
    """
    super().__init__(*args, **kwargs)

    # title
    self._title_field = InputText(
      label=title_field_name, 
      value=title_field_value, 
      min_length=min_title_size,
      max_length=max_title_size,
      style=InputTextStyle.short
    )
    self.add_item(self._title_field)
    
    # content
    self._content_field = InputText(
      label=content_field_name, 
      value=content_field_value, 
      min_length=min_content_size,
      max_length=max_content_size,
      style=InputTextStyle.long
    )
    self.add_item(self._content_field)

    # callback(interaction, title, field), should also send response
    self._submit_callback = submit_callback
    
  async def callback(self, interaction: Interaction):
    try:
      await self._submit_callback(interaction, self._title_field.value, self._content_field.value)
    except InvalidArgument as e:
      await interaction.response.send_message(content="cannot submit modal", ephemeral=True)



class ListEmbed(Embed):
  def __init__(self, items, *args, max_items=-1, **kwargs):
    if max_items > 0:
      self._items = items[:max_items]
    else: 
      self._items = items
    description = "\n".join([self._item_desc(i, item) for i, item in enumerate(self._items)])
    if max_items > 0 and len(items) > max_items:
      description = "*" + _t("general.ui.list.toomany", count=max_items) + "*\n\n" + description
    super().__init__(
      *args,
      description=description,
      **kwargs)

  @abstractmethod
  def _elem_desc(self, index, item):
    pass