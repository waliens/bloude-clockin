from discord import ButtonStyle, Interaction, InvalidArgument
from discord.ui import View, Button

from db_util.item import register_loot, register_recipe
from lang.util import localized_attr
from models import Item, Loot, Recipe
from ui.util import CancelButton, ListEmbed, ListSelectorView

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


class LootListSelectorView(ListSelectorView):
  def __init__(self, bot, items, character_id, *args, max_items=-1, **kwargs):
    super().__init__(bot, items, *args, max_elems=max_items, **kwargs)
    self._character_id = character_id
  
  async def button_click_callback(self, sess, elem):
    await register_loot(sess, elem.id, self._character_id)

  def success_message(self):
    return _t("item.add.success")

  def error_message(self, error: InvalidArgument):
    return _t("loot.add.error", error=str(error))


class RecipeListSelectorView(ListSelectorView):
  def __init__(self, bot, recipes, character_id, *args, max_recipes=-1, **kwargs):
    super().__init__(bot, recipes, *args, max_elems=max_recipes, **kwargs)
    self._character_id = character_id
  
  async def button_click_callback(self, sess, elem):
    await register_recipe(sess, elem.id, self._character_id)

  def success_message(self):
    return _t("recipe.add.success")

  def error_message(self, error: InvalidArgument):
    return _t("recipe.add.error", error=str(error))

