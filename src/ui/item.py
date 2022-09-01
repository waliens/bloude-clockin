from discord import ButtonStyle, Interaction, InvalidArgument, Embed
from discord.ui import View, Button

from db_util.item import get_crafters, register_loot, register_recipe
from db_util.wow_data import ProfessionEnum
from lang.util import localized_attr
from models import Item, Loot, Recipe
from ui.util import ListEmbed, ListSelectorView

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
    return {"content": _t("item.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("loot.add.error", error=str(error)), "embed": None, "view": None}


class RecipeRegistrationListSelectorView(ListSelectorView):
  def __init__(self, bot, recipes, character_id, *args, max_recipes=-1, **kwargs):
    super().__init__(bot, recipes, *args, max_elems=max_recipes, **kwargs)
    self._character_id = character_id
  
  async def button_click_callback(self, sess, elem):
    await register_recipe(sess, elem.id, self._character_id)

  def success_message(self):
    return {"content": _t("recipe.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("recipe.add.error", error=str(error)), "embed": None, "view": None}


class RecipeRegistrationListSelectorView(ListSelectorView):
  def __init__(self, bot, recipes, character_id, *args, max_recipes=-1, **kwargs):
    super().__init__(bot, recipes, *args, max_elems=max_recipes, **kwargs)
    self._character_id = character_id
  
  async def button_click_callback(self, sess, recipe):
    await register_recipe(sess, recipe.id, self._character_id)

  def success_message(self):
    return {"content": _t("recipe.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("recipe.add.error", error=str(error)), "embed": None, "view": None}


def profession_emoji(profession: ProfessionEnum):
  return {
    ProfessionEnum.LEATHERWORKING: ":mans_shoe:",
    ProfessionEnum.TAILORING: ":sewing_needle:",
    ProfessionEnum.ENGINEERING: ":wrench:",
    ProfessionEnum.BLACKSMITHING: ":hammer:",
    ProfessionEnum.COOKING: ":fondue:",
    ProfessionEnum.ALCHEMY: ":alembic:",
    ProfessionEnum.FIRST_AID: ":adhesive_bandage:",
    ProfessionEnum.ENCHANTING: ":magic_hand:",
    ProfessionEnum.FISHING: ":fish:",
    ProfessionEnum.JEWELCRAFTING: ":ring:",
    ProfessionEnum.INSCRIPTION: ":scroll:",
    ProfessionEnum.MINING: ":pick:",
    ProfessionEnum.HERBALISM: ":herb:",
    ProfessionEnum.SKINNING: ":beaver:"
  }.get(profession, "?")



class RecipeCraftersEmbed(Embed):
  def __init__(self, crafters, *args, show_ids=False, max_crafters_per_recipe=10, **kwargs):
    super().__init__(*args, title=_t("recipe.crafters.embed.title"), **kwargs)
    self._crafters = crafters
    self._max_crafters_per_recipe = max_crafters_per_recipe
    self._show_ids = show_ids

    for recipe, characters in self._crafters: 
      self.add_field(**self._get_field_data(recipe, characters))    

  def _get_field_data(self, recipe, characters):
    name = ""
    if self._show_ids:
      name += f"`[{recipe.id}]` "
    name += localized_attr(recipe, "name")
    name += f"  {profession_emoji(recipe.profession)}"

    if len(characters) == 0:
      value = _t("recipe.crafters.embed.field.no_crafter")
    else:
      # filter characters (one per user, preferably the main )
      actual_characters = dict()
      for character in characters:
        if character.id in actual_characters and not character.is_main:
          continue
        actual_characters[character.id] = character
    
      # generate text
      # value = _t("recipe.crafters.embed.field.crafters_count", count=len(characters)) + "\n"
      value = "\n".join([f"- {character.name} <@{character.id_user}>" for character in list(actual_characters.values())[:self._max_crafters_per_recipe]]) 

    return  {"inline": False, "name": name, "value": value}


class RecipeCraftersListSelectorView(ListSelectorView):
  def __init__(self, bot, recipes, *args, show_ids=False, max_recipes=-1, **kwargs):
    super().__init__(bot, recipes, *args, max_elems=max_recipes, **kwargs)
    self._show_ids = show_ids
    self._crafters = []

  async def button_click_callback(self, sess, recipe):
    self._crafters = await get_crafters(sess, [recipe.id])

  def success_message(self):
    embed = RecipeCraftersEmbed(self._crafters, show_ids=self._show_ids)
    return {"embed": embed, "view": None, "content": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("recipe.add.error", error=str(error)), "embed": None, "view": None}




