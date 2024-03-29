

from abc import abstractmethod
from functools import partial
from discord.ui import Button, Select, Modal, InputText, View
from discord import ButtonStyle, InputTextStyle, Interaction, InvalidArgument, SelectOption, Embed

from pycord18n.extension import _ as _t

EMBED_FIELD_NAME_MAX_LENGTH = 256
EMBED_FIELD_VALUE_MAX_LENGTH = 1024
EMBED_DESCRIPTION_MAX_LENGTH = 4096


class NoSelectionException(InvalidArgument):
  def __init__(self, *args: object) -> None:
    super().__init__(_t("general.invalid.no_selection"), *args)


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


class ConfirmButton(Button):
  def __init__(self, confirm_callback=None, *args, **kwargs):
    super().__init__(style=ButtonStyle.primary, label=_t("general.confirm"), *args, **kwargs)
    self._confirm_callback = confirm_callback

  @property
  def confirm_callback(self):
    return self._confirm_callback
  
  @confirm_callback.setter
  def confirm_callback(self, clbk):
    self._confirm_callback = clbk

  async def callback(self, interaction: Interaction):
    await self._confirm_callback(interaction)


class ConfirmAndContinueButton(Button):
  def __init__(self, confirm_callback=None, *args, **kwargs):
    super().__init__(style=ButtonStyle.primary, label=_t("general.confirm_and_continue"), *args, **kwargs)
    self._confirm_callback = confirm_callback

  @property
  def confirm_callback(self):
    return self._confirm_callback
  
  @confirm_callback.setter
  def confirm_callback(self, clbk):
    self._confirm_callback = clbk

  async def callback(self, interaction: Interaction):
    await self._confirm_callback(interaction)


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
    if len(self._items) > 0:
      description = "\n".join([self._item_desc(i, item) for i, item in enumerate(self._items)])
      if max_items > 0 and len(items) > max_items:
        description = "*" + _t("general.ui.list.toomany", count=max_items) + "*\n\n" + description
    else:
      description = "*" + _t("general.ui.list.empty") + "*"
    super().__init__(
      *args,
      description=description,
      **kwargs)

  @abstractmethod
  def _elem_desc(self, index, item):
    pass


class ListSelectionButton(Button):
  def __init__(self, bot, elem_nb, elem, handle_clbk, success_msg_clbk, error_msg_clbk, *args, **kwargs):
    """
    bot: GCIBot
      The bot
    elem_nb: int
      The number to select by clicking the button
    handle_clbk: coroutine
      Handles the elem selection. Receives the db session as first argument and the selected element as second.
    success_msg_clbk: callable
      Returns the success message
    error_msg_clbk: callable
      Returns the error message. Receives the InvalidArgument exception as first argument.
    """
    super().__init__(*args, label=f"{elem_nb}", style=ButtonStyle.primary, **kwargs)
    self._elem = elem
    self._handle_clbk = handle_clbk
    self._success_msg_clbk = success_msg_clbk
    self._error_msg_clbk = error_msg_clbk
    self._bot = bot

  async def callback(self, interaction: Interaction):
    try:
      self.view.disable_all_items()
      async with self._bot.db_session_class() as sess:
        async with sess.begin():
          await self._handle_clbk(sess, self._elem)
      self.view.stop()
      self.view.clear_items()
      await interaction.response.edit_message(**self._success_msg_clbk())
    except InvalidArgument as e:
      self.view.enable_all_items()
      return await interaction.response.edit_message(**self._error_msg_clbk(e))


class ListSelectorView(View):
  def __init__(self, bot, elems, *args, max_elems=-1, **kwargs):
    """
    bot: GCIBot
    elems: list
      List of elements to be selected.
    max_elems: int
      Maximum number of elements to display in the selection view.
    """
    super().__init__(*args, **kwargs)
    if max_elems > 0:
      self._elems = elems[:max_elems]
    else: 
      self._elems = elems

    self._buttons = [
      ListSelectionButton(bot, i+1, elem, self.button_click_callback, self.success_message, self.error_message) 
      for i, elem in enumerate(self._elems)
    ]

    for button in self._buttons:
      self.add_item(button)
    self.add_item(CancelButton())

  @abstractmethod
  async def button_click_callback(self, sess, item):
    pass

  @abstractmethod
  def success_message(self):
    pass

  @abstractmethod
  def error_message(self, error: InvalidArgument):
    pass


class MultiSelectView(View):
  def __init__(self, bot, selects, *args, check_for_values=True, allow_multiple=False, **kwargs):
    super().__init__(*args, **kwargs)
    self._bot = bot
    self._selects = selects
    self._cancel_button = CancelButton()
    self._check_for_values = check_for_values
    self._allow_multiple = allow_multiple

    async def _confirm_callback(interaction: Interaction, repeat: bool=False):
      try:
        self.disable_all_items()
        selected_values = [select.values for select in self._selects]
        if self._check_for_values and any(len(vs) == 0 for vs in selected_values):
          raise NoSelectionException()

        if self._allow_multiple and repeat:
          await self.confirm_callback(*selected_values)
          self.enable_all_items()
          await interaction.response.edit_message()
        else:
          await self.confirm_callback(*selected_values)
          self.stop()
          self.clear_items()
          await interaction.response.edit_message(**self.success_message())

      except NoSelectionException as e:
        self.enable_all_items()
        return await interaction.response.edit_message(content=str(e))
      except InvalidArgument as e:
        self.enable_all_items()
        return await interaction.response.edit_message(**self.error_message(e))
      
    self._validate_button = ConfirmButton(confirm_callback=_confirm_callback)

    for select in self._selects:
      self.add_item(select)
    self.add_item(self._validate_button)
    
    if self._allow_multiple:
      self._validate_and_continue_button = ConfirmAndContinueButton(confirm_callback=partial(_confirm_callback, repeat=True))
      self.add_item(self._validate_and_continue_button)
    
    self.add_item(self._cancel_button)

  @abstractmethod
  async def confirm_callback(self, *values):
    pass

  @abstractmethod
  def success_message(self):
    pass

  @abstractmethod
  def error_message(self, error: InvalidArgument):
    pass

  @property
  def bot(self):
    return self._bot 
