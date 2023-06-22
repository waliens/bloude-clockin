from discord import ButtonStyle, Interaction, InvalidArgument, Embed
from discord.ui import View, Button

from db_util.item import get_crafters, register_loot, register_user_recipes
from db_util.wow_data import MainStatusEnum, ProfessionEnum
from lang.util import localized_attr
from models import GuildCharterField, Item, Loot, Recipe
from ui.util import EMBED_DESCRIPTION_MAX_LENGTH, EMBED_FIELD_VALUE_MAX_LENGTH, ListEmbed, ListSelectorView

from pycord18n.extension import _ as _t


class ItemListEmbed(ListEmbed):
  def _item_desc(self, index, item: Item):
    desc = f"`{index+1}` ({item.metadata_['ItemLevel']}) {localized_attr(item, 'name')}"
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
    if loot.in_dkp:
      desc += ":lock: " 
    if self._show_ids:
      desc += f"`[{loot.item.id}]` "
    desc += f"({loot.item.metadata_['ItemLevel']}) {localized_attr(loot.item, 'name')}"
    if loot.item.metadata_["Flags"] & 0x8:
      desc += " (H)"
    datetime_to_display = loot.created_at
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


def get_profession_emoji(profession: ProfessionEnum):
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


class UserRecipeEmbed(Embed):
  ETC_DESC = "..."

  def __init__(self, character, user_recipes, *args, one_profession: ProfessionEnum=None, show_ids=False, show_dates=False, **kwargs):
    super().__init__(*args, **kwargs)
    self._show_ids = show_ids
    self._show_dates = show_dates
    self._one_profession = one_profession

    if self._one_profession is None:
      self.title = _t("recipe.recipes")
      self.description = _t("recipe.ui.user_recipe.embed.description", char_name=character.name, id_user=character.id_user)
      for profession in {ur.recipe.profession for ur in user_recipes}:
        self.add_field(**self._get_profession_field(profession, user_recipes))
    else:
      self.title = _t("recipe.ui.user_recipe.embed.title.one_prof", 
        emoji=get_profession_emoji(self._one_profession), 
        prof_name=self._one_profession.name_hr, 
        char_name=character.name
      )
      self.description = f"<@{character.id_user}>\n"
      self.description += self._get_all_recipes_list(user_recipes, size_limit=EMBED_DESCRIPTION_MAX_LENGTH - len(self.description))

  def _get_all_recipes_list(self, user_recipes, size_limit=EMBED_DESCRIPTION_MAX_LENGTH):
    if len(user_recipes) == 0:
      return _t("recipe.ui.user_recipe.embed.no_recipe")
    recipe_descriptors = list()
    for ur in sorted(user_recipes, key=lambda r: localized_attr(r.recipe, "name")):
      desc = self._get_user_recipe_descriptor(ur)
      # check if going over field content size limit
      curr_field_size = sum(map(len, recipe_descriptors)) + len(recipe_descriptors) 
      if curr_field_size + len(desc) < size_limit - len(self.ETC_DESC):
        recipe_descriptors.append(desc)
      else:
        recipe_descriptors.append(self.ETC_DESC)
        break
    return "\n".join(recipe_descriptors)
  
  def _get_profession_field(self, profession: ProfessionEnum, user_recipes, size_limit=EMBED_FIELD_VALUE_MAX_LENGTH):
    filtered = [ur for ur in user_recipes if ur.recipe.profession == profession]
    name = f"{profession.name_hr} {get_profession_emoji(profession)}"

    recipe_descriptors = list()
    for ur in sorted(filtered, key=lambda r: localized_attr(r.recipe, "name")):
      desc = self._get_user_recipe_descriptor(ur)
      # check if going over field content size limit
      curr_field_size = sum(map(len, recipe_descriptors)) + len(recipe_descriptors) 
      if curr_field_size + len(desc) < size_limit - len(self.ETC_DESC):
        recipe_descriptors.append(desc)
      else:
        recipe_descriptors.append(self.ETC_DESC)
        break
    
    if len(filtered) == 0:
      value = _t("recipe.ui.user_recipe.embed.no_recipe")
    else:
      value = "\n".join(recipe_descriptors)

    return {"name": name, "value": value, "inline": False}

  def _get_user_recipe_descriptor(self, user_recipe):
    desc = ""
    if self._show_ids:
      desc = f"`[{user_recipe.recipe.id}]` "
    else:
      desc = "- "
    desc += f"{localized_attr(user_recipe.recipe, 'name')}"
    if self._show_dates:
      desc += f" ({user_recipe.created_at.strftime('%d/%m/%Y')})"
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
    await register_user_recipes(sess, [elem.id], self._character_id)

  def success_message(self):
    return {"content": _t("recipe.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("recipe.add.error", error=str(error)), "embed": None, "view": None}


class RecipeRegistrationListSelectorView(ListSelectorView):
  def __init__(self, bot, recipes, character_id, *args, max_recipes=-1, **kwargs):
    super().__init__(bot, recipes, *args, max_elems=max_recipes, **kwargs)
    self._character_id = character_id
  
  async def button_click_callback(self, sess, recipe):
    await register_user_recipes(sess, [recipe.id], self._character_id)

  def success_message(self):
    return {"content": _t("recipe.add.success"), "embed": None, "view": None}

  def error_message(self, error: InvalidArgument):
    return {"content": _t("recipe.add.error", error=str(error)), "embed": None, "view": None}


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
    name += f" {get_profession_emoji(recipe.profession)}"

    if len(characters) == 0:
      value = _t("recipe.crafters.embed.field.no_crafter")
    else:
      # filter characters (one per user, preferably the main )
      actual_characters = dict()
      for character in characters:
        if character.id in actual_characters and not character.main_status == MainStatusEnum.MAIN:
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




