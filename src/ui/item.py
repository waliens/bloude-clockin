from discord import ButtonStyle, Interaction, InvalidArgument
from discord.ui import View, Button

from db_util.item import register_loot
from lang.util import localized_attr
from models import Item, Loot, Recipe
from ui.util import CancelButton, ListEmbed

from pycord18n.extension import _ as _t


class ItemListEmbed(ListEmbed):
  def _item_desc(self, index, item: Item):
    desc = f"`{index+1}` {localized_attr(item, 'name')}"
    if item.metadata_["Flags"] & 0x8:
      desc += " (H)"
    return desc


class LootListEmbed(ListEmbed):
  def __init__(self, *args, show_ids=False, **kwargs):
    self._show_ids = show_ids 
    super().__init__(*args, **kwargs)

  def _item_desc(self, index, item: Loot):
    loot = item
    desc = f"`{index+1}` "
    if loot.count > 1:
      desc += f"**{loot.count}x** "
    if self._show_ids:
      desc += f"`[{loot.item.id}]` "
    desc += f"{localized_attr(loot.item, 'name')}"
    if loot.item.metadata_["Flags"] & 0x8:
      desc += " (H)"
    datetime_to_display = loot.updated_at if loot.updated_at is not None else loot.created_at
    desc += f" - {datetime_to_display.strftime('%d/%m/%Y')}"
    return desc


class RecipeListEmbed(ListEmbed):
  def __init__(self, *args, show_ids=False, **kwargs):
    self._show_ids = show_ids 
    super().__init__(*args, **kwargs)

  def _item_desc(self, index, item: Recipe):
    recipe = item
    desc = f"`{index+1}` "
    if self._show_ids:
      desc += f"`[{recipe.id}]` "
    desc += f"{localized_attr(recipe, 'name')}"
    desc += f" ({recipe.profession.name_hr.lower()})"
    return desc


class LootSelectionButton(Button):
  def __init__(self, bot, item_nb, item_id, character_id, *args, **kwargs):
    super().__init__(*args, label=f"{item_nb}", style=ButtonStyle.primary, **kwargs)
    self._bot = bot
    self._item_id = item_id
    self._character_id = character_id

  async def callback(self, interaction: Interaction):
    try:
      self.view.disable_all_items()
      async with self._bot.db_session_class() as sess:
        async with sess.begin():
          await register_loot(sess, self._item_id, self._character_id)
      self.view.stop()
      self.view.clear_items()
      await interaction.response.edit_message(content=_t("item.add.success"), view=None, embed=None)
    except InvalidArgument as e:
      self.view.enable_all_items()
      return await interaction.response.edit_message(content=_t("loot.add.error", error=str(e)), view=None, embed=None)


class LootListSelectorView(View):
  def __init__(self, bot, items, character_id, *args, max_items=-1, **kwargs):
    super().__init__(*args, **kwargs)
    self._bot = bot
    self._character_id = character_id
    if max_items > 0:
      self._items = items[:max_items]
    else: 
      self._items = items

    self._buttons = [
      LootSelectionButton(self._bot, i+1, item.id, self._character_id) 
      for i, item in enumerate(self._items)
    ]

    for button in self._buttons:
      self.add_item(button)
    self.add_item(CancelButton())


    