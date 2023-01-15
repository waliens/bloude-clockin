from collections import defaultdict
from enum import Enum
from pygsheets import Cell
from sqlalchemy import select
from db_util.wow_data import ItemInventoryTypeEnum

from models import Character, Item, Loot


class ParseError(Exception):
  def __init__(self, row, col, parent=None, ws=None) -> None:
    super().__init__(parent)
    self._parent = parent
    self._row = row
    self._col = col
    self._ws = ws
    self._cell = Cell((row, col), worksheet=ws)
  
  def __str__(self) -> str:
    cell_addr = f"{self._cell.label}"
    if self._ws is not None:
      cell_addr = f"'{self._ws.title}'!" + cell_addr
    return f"cell \"{cell_addr}\": {str(self._parent)}."
  
  @property
  def row(self):
    return self._row

  @property
  def col(self):
    return self._col

  @property
  def worksheet(self):
    return self._ws
  
  @worksheet.setter
  def worksheet(self, value):
    self._cell = Cell((self._row, self._col), worksheet=value)  
    self._ws = value


class PriorityError(Exception):
  def __init__(self, col_index, desc, *args):
    super().__init__(desc, *args)
    self._col_index = col_index
  
  @property
  def col_index(self):
    return self._col_index


class InvalidSepError(PriorityError):
  def __init__(self, col_index, sep, *args) -> None:
    super().__init__(col_index, f"expected separator, got '{sep}'", *args)
    self._sep = sep

  @property
  def sep(self):
    return self._sep


class DuplicateRoleError(PriorityError):
  def __init__(self, col_index, duplicate, *args) -> None:
    super().__init__(col_index, f"duplicate role {duplicate}", *args)
    self._duplicate = duplicate

  @property
  def duplicate(self):
    return self._duplicate


class PrioTierEnum(Enum):
  IS_BIS = 5
  IS_ALMOST_BIS = 15
  IS_AVERAGE = 25
  IS_A_UP = 35
  IS_USELESS = 100 

  @staticmethod
  def useful_tiers():
    return [
      PrioTierEnum.IS_BIS,
      PrioTierEnum.IS_ALMOST_BIS,
      PrioTierEnum.IS_AVERAGE,
      PrioTierEnum.IS_A_UP
    ]

class SepEnum(Enum):
  TIER = ">>"
  BETTER = ">"
  EQUAL = "~"

  @classmethod
  def is_valid(cls, v):
    return v in {e.value for e in cls}


def enum_get(e: Enum, k, default=None):
  try:
    return e[k]
  except KeyError:
    return default


class PriorityList(object):

  def __init__(self, prio_array: list) -> None:
    self._priorities = self._parse(prio_array)

  def has_roles(self):
    return any([self.tier_has_roles(tier) for tier in self._priorities.keys()])

  def tier_has_roles(self, tier):
    return sum([len(sublevel) for sublevels in self._priorities.get(tier, []) for sublevel in sublevels]) > 0

  def _parse(self, array):
    prios = defaultdict(list)
    already_processed = set()
    curr_index = 0
    for curr_tier in PrioTierEnum.useful_tiers():
      prios[curr_tier].append(set())
      while curr_index < len(array):
        elem = array[curr_index]
        curr_index += 1
        if elem is None:
          continue
        if isinstance(elem, str):  # sep:
          if elem == SepEnum.TIER.value or elem is None or len(elem.strip()) == 0:
            break
          elif elem == SepEnum.EQUAL.value:
            continue
          elif elem == SepEnum.BETTER.value:
            prios[curr_tier].append(set())
          else: raise InvalidSepError(curr_index, elem)
        else:
          if elem in already_processed:
            raise DuplicateRoleError(curr_index, elem)
          already_processed.add(elem)
          prios[curr_tier][-1].add(elem)
    return prios

  def get_priority_tier(self, query: tuple):
    for tier_prio, sublevels in self._priorities.items():
      for level in sublevels:
        if query in level:
          return tier_prio
    return PrioTierEnum.IS_USELESS

  def get_for_tier(self, tier: PrioTierEnum):
    return self._priorities[tier]
  
  def cmp(self, query1: tuple, query2: tuple):
    """
    q1 < q2 => return negative
    q1 = q2 => return 0
    q1 > q2 => return positive
    """ 
    prio1 = self.get_priority_tier(query1)
    prio2 = self.get_priority_tier(query2)
    if prio1 != prio2:
      return prio2.value - prio1.value
    else:
      sublevels = self._priorities[prio1]
      index1, index2 = None, None
      for i, sublevel in enumerate(sublevels):
        if query1 in sublevel:
          index1 = i
        if query2 in sublevel: 
          index2 = i
      return index2 - index1

  def is_better(self, query1, query2):
    """is query1 better than query2?"""
    return self.cmp(query1, query2) > 0

  def is_equiv(self, query1, query2):
    return self.cmp(query1, query2) == 0


class ItemWithPriority(object):
  def __init__(self, item_id: int, priority_list: PriorityList, **metadata):
    self._item_id = item_id
    self._priority_list = priority_list
    self._metadata = metadata

  @property 
  def priority_list(self):
    return self._priority_list

  @property
  def metadata(self):
    return self._metadata


def empty_prio_str_dict():
  return {}


def format_role_list(roles, role_names_map: dict):
  return [role_names_map.get(role, "???") for role in roles]


async def generate_prio_str_for_item(sess, id_guild, item: Item, item_priority: ItemWithPriority, item_level: int, role_names_map: dict= None, character_map: dict = None, user_dkp_map: dict = None, loots_per_char: dict = None):
  """
  Parameters
  ----------
  sess: AsyncSession
  id_guild: int
    Guild identifier
  item: Item
    The item
  item_priority: ItemWithPriority
    An item with its priority
  item_level: int 
    The item level of the item
  role_names_map: ???
    Map a role tuple with its actual name
  characters_map: dict
    Maps role tuple with a list of characters
  user_dkp_map: dict
    Maps a user identifier with its dkp score
  loots_per_char: dict
    Maps character id with its loots for the slot if the item

  Returns
  -------
  prio_dict: dict
    Maps prio tier enum to it prioritized list of players/roles
  """
  item_id = item.id
  item_slot = ItemInventoryTypeEnum(item.metadata_["InventoryType"]).get_slot()
  priority = item_priority._priority_list
  if not priority.has_roles():
    return empty_prio_str_dict()

  if character_map is None:
    return {
      tier: " > ".join([" = ".join(format_role_list(sublevel, role_names_map)) for sublevel in priority.get_for_tier(tier) if len(sublevel) > 0]) 
      for tier in PrioTierEnum
      if priority.tier_has_roles(tier)
    }

  if loots_per_char is None:
    loots_per_char = defaultdict(list)
  
  # consider already looted items
  already_looted_query = select(Loot).where(Loot.id_item == item_id, Loot.character.has(Character.id_guild == id_guild))
  already_looted_results = await sess.execute(already_looted_query)
  curr_item_loots = already_looted_results.scalars().all()
  characters_have_looted = {loot.id_character for loot in curr_item_loots}

  prio_str_dict = dict()
  for tier in PrioTierEnum:
    tier_sublevels = priority.get_for_tier(tier)
    if not priority.tier_has_roles(tier):
      continue
    
    tier_characters = list()
    for sublevel in tier_sublevels:
      sublevel_characters = list()
      for role in sublevel:
        found_characters = list()
        for char, _ in sorted(character_map[role], key=lambda t: t[0].main_status.value): 
          user_dkp = user_dkp_map[char.id_user]
          # has looted the same item ?
          if char.id in characters_have_looted:
            continue
          char_ilvl = "-"
          if len(loots_per_char[char.id]) > 0:
            best_loot, _ = loots_per_char[char.id][0]
            char_ilvl = str(best_loot.item.metadata_["ItemLevel"])
          # has looted an upgrade ? (only if equippable and not a bis)
          if item_slot is not None and tier is not PrioTierEnum.IS_BIS and len(loots_per_char[char.id]) > 0:
            char_loots = loots_per_char[char.id]
            best_loot, best_loot_tier = char_loots[0]
            if tier.value >= best_loot_tier.value and item_level <= best_loot.item.metadata_["ItemLevel"]:
              continue 
          found_characters.append(f"{char.name} ({user_dkp}, {char_ilvl})")
        sublevel_characters.extend(found_characters)
      if len(sublevel_characters) == 0:
        continue
      tier_characters.append(" = ".join(sublevel_characters))
    if len(tier_characters) == 0:
      continue
    prio_str_dict[tier] = " > ".join(tier_characters)
  
  return prio_str_dict