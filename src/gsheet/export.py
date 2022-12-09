import pygsheets

from collections import defaultdict
from pygsheets import Spreadsheet, Worksheet, Cell, DataRange
from discord import Guild, InvalidArgument, Client, Role
from sqlalchemy import select, Integer
from db_util.dkp import compute_dkp_score
from db_util.priorities import PrioTierEnum, generate_prio_str_for_item
from db_util.raid_helper import extract_raid_helpers_data
from db_util.wow_data import ItemInventoryTypeEnum, MainStatusEnum
from gsheet.parse_priorities import PrioParser
from gsheet_helpers import get_creds
from models import Character, GuildSettings, Item, Loot
from pycord18n.extension import _ as _t
from lang.util import localized_attr
from db_util.wow_data import InventorySlotEnum, ItemInventoryTypeEnum


def create_worksheet(sheet: Spreadsheet, name: str, table) -> Worksheet:
  """
  table: list
    List of list representing a 2D array (rows first).

  Returns
  -------
  worksheet: Worksheet
    The resulting worksheet
  """
  worksheets = sheet.worksheets()
  try:
    idx = [wk.title for wk in worksheets].index(name)
    worksheet = worksheets[idx]
    worksheet.clear(fields="*")
    DataRange(worksheet=worksheet).merge_cells(merge_type='NONE')
  except ValueError:
    worksheet = sheet.add_worksheet(name)

  worksheet.rows = len(table) + 1
  worksheet.update_values("A1", table) 

  return worksheet


async def create_characters_table(sess, guild_id):
  table = list()

  # headers
  headers = ["name", "class", "role", "spec", "main", "user"]
  table.append(headers)

  # content
  query = select(Character).where(Character.id_guild == guild_id)
  results = await sess.execute(query)
  characters = results.scalars().all()

  for character in characters:
    table.append([
      character.name,
      character.character_class.name,
      character.role.name,
      "" if character.spec is None else character.spec.name,
      character.main_status.name_hr,
      character.id_user
    ])
  
  return table

async def create_loot_table(sess, guild_id):
  table = list()

  # headers
  headers = ["character", "id", "name_en", "name_fr", "count", "date", "user"]
  table.append(headers)

  # content
  query = select(Loot).where(Loot.character.has(id_guild=guild_id))
  results = await sess.execute(query)
  loots = results.scalars().all()

  for loot in loots:
    table.append([
      loot.character.name,
      loot.item.id,
      loot.item.name_en,
      loot.item.name_fr,
      loot.created_at.strftime('%d/%m/%Y %H:%M'),
      loot.character.id_user
    ])
  
  return table


async def loots_for_slots(sess, slot: InventorySlotEnum, char_map: dict, priorities: dict):
  """Returs a dictionnary mapping character ids with list of tuples (=> [loot, tier level] )for this slot sorted by increasing priority tier and deacreasing ilvl

  """
  # extract loots for all listed characters and given slot
  if slot is None:
    inv_types = [ItemInventoryTypeEnum.NON_EQUIPABLE]
  else:
    inv_types = slot.get_inventory_types()
  query = select(Loot).where(
    Loot.item.has(Item.metadata_['InventoryType'].astext.cast(Integer).in_([it.value for it in inv_types])),
    Loot.id_character.in_([char.id for char_list in char_map.values() for char, _ in char_list]),
    Loot.id_item.in_(list(priorities.keys()))
  )
  results = await sess.execute(query)
  loots = results.scalars().all()

  # group per character and filter out items that are not useful
  loot_per_character = defaultdict(list)
  for loot in loots:
    priority_list = priorities[loot.id_item].priority_list
    tier = priority_list.get_priority_tier(loot.character.role_tuple)
    if tier != PrioTierEnum.IS_USELESS:
      loot_per_character[loot.id_character].append((loot, tier))

  # sort by tier and ilvl
  for id_character in loot_per_character.keys():
    loots = loot_per_character[id_character]
    # sort by increasing priority tier (first) and item level deacreasing (second)
    sort_key_fn = lambda loot_tuple: (
      loot_tuple[1].value,
      -int(loot_tuple[0].item.metadata_['ItemLevel'])
    )
    loot_per_character[id_character] = sorted(loots, key=sort_key_fn)
  
  return loot_per_character


async def generate_prio_sheets(sess, client: Client, gc, sheet, guild: Guild, priorities: dict, role2name: dict, for_event: str=None, phase: int=-1):
  """
  Parameters
  ----------
  sheet: pygsheets.SpreadSheet
    The worksheet will be generated/replaced here
  id_guild: [int|str]
    Guild identifier
  priorities: Mapping[int,ItemWithPriority]
  role2name: Mapping[tuple,str]
    Maps role tuples with its str name
  for_event: str
    Only use users from a RaidHelper event (ignoring role filtering if set)
  phase: int
    A phase number, only items from this phase will be displayed. -1 for last phase only, 0 for all phases.
  """
  # read main characters list
  where_clause = [Character.main_status != MainStatusEnum.OTHER, Character.id_guild == str(guild.id)]

  # role filtering
  settings = await sess.get(GuildSettings, str(guild.id))
  id_prio_role = settings.id_prio_role

  if for_event is not None:
    _, registered, _ = await extract_raid_helpers_data(sess, int(for_event), str(guild.id))
    where_clause.append(Character.id.in_([character.id for character in registered]))
  elif id_prio_role is not None:
    role = guild.get_role(int(settings.id_prio_role))
    user_ids = [str(member.id) for member in role.members]
    if len(user_ids) > 0:  # only if there are actually users with this tag
      where_clause.append(Character.id_user.in_(user_ids))

  query = select(Character).where(*where_clause)
  results = await sess.execute(query)

  characters = results.scalars().all()
  char_dict = defaultdict(list)
  for char in characters:
    char_dkp = await compute_dkp_score(sess, char, priorities)
    char_dict[(char.character_class, char.role, char.spec)].append((char, char_dkp))

  user_dkp_dict = defaultdict(lambda: 0)
  for characters in char_dict.values():
    for char, dkp in characters:
      user_dkp_dict[char.id_user] += dkp

  # generate sheet table 
  per_class_sheet_table = list()
  per_char_sheet_table = list()
  headers = [
    _t("prio.gsheet.col.id"), 
    _t("prio.gsheet.col.name"),
    _t("prio.gsheet.col.ilvl"), 
    _t("prio.gsheet.col.bis"),
    _t("prio.gsheet.col.almost_bis"), 
    _t("prio.gsheet.col.average"), 
    _t("prio.gsheet.col.is_up")
  ]
  per_class_sheet_table.append(headers)
  per_char_sheet_table.append(headers)
  
  item_index = dict()
  per_slot = defaultdict(list)

  for item_id in priorities.keys():
    item = await sess.get(Item, item_id)
    if item is None:
      continue
    item_index[item_id] = item
    inventory_type = ItemInventoryTypeEnum(item.metadata_["InventoryType"])
    per_slot[inventory_type.get_slot()].append(item_id)

  # check phase
  if phase == -1:
    phase = max([prio.metadata["phase"] for prio in priorities.values()])
  
  slot_header_cell_merges = list()
  for slot, item_ids in per_slot.items():
    current_row = len(per_class_sheet_table) + 1
    slot_header_cell_merges.append(current_row)
    loots_per_character = await loots_for_slots(sess, slot, char_dict, priorities)

    # read current item lists
    if slot is not None:
      per_class_sheet_table.append([slot.name_hr])
      per_char_sheet_table.append([slot.name_hr])
    else:
      per_class_sheet_table.append([ItemInventoryTypeEnum.NON_EQUIPABLE.name_hr])
      per_char_sheet_table.append([ItemInventoryTypeEnum.NON_EQUIPABLE.name_hr])

    for item_id in item_ids:
      if phase != 0 and priorities[item_id].metadata["phase"] != phase:
        continue
      item = item_index[item_id]
      row_header = [item.id, localized_attr(item, 'name'), item.metadata_["ItemLevel"]]
      # per_class
      per_class_prio_dict = await generate_prio_str_for_item(
        sess, str(guild.id), 
        item, priorities[item_id], 
        item.metadata_["ItemLevel"], 
        role2name, 
        loots_per_char=loots_per_character)
      per_class_sheet_table.append(row_header + [per_class_prio_dict.get(t, " ") for t in PrioTierEnum.useful_tiers()])
      # per char
      per_char_prio_dict = await generate_prio_str_for_item(
        sess, str(guild.id), 
        item, priorities[item_id], 
        item.metadata_["ItemLevel"], 
        role2name, 
        char_dict, user_dkp_dict, 
        loots_per_char=loots_per_character)
      per_char_sheet_table.append(row_header + [per_char_prio_dict.get(t, " ") for t in PrioTierEnum.useful_tiers()])

  # actually generate the sheet
  wksheets = list()
  for sheet_name, sheet_table in [("gci_prio", per_char_sheet_table), ("gci_prio_class", per_class_sheet_table)]: 
    wks = create_worksheet(sheet, name=sheet_name, table=sheet_table)
    wksheets.append(wks)
    gc.set_batch_mode(True)
    # formatting
    reference_style_cell = Cell("A1", worksheet=wks)
    reference_style_cell.color = (0.576, 0.769, 0.49, 0)

    for row_number in slot_header_cell_merges:
      row = wks.get_row(row_number, returnas="range")
      row.merge_cells()
      row.apply_format(reference_style_cell, fields="userEnteredFormat.backgroundColor")

    reference_style_cell.color = (0.22, 0.463, 0.114, 0)
    reference_style_cell.set_text_format("bold", True)
    reference_style_cell.set_text_format("foregroundColor", (1, 1, 1, 0))
    wks.get_row(1, returnas="range").apply_format(reference_style_cell)
    gc.run_batch()
    gc.set_batch_mode(False)
  
  return wksheets


async def export_in_worksheets(sess, client: Client, guild: Guild, for_event: str=None):
  settings = await sess.get(GuildSettings, str(guild.id))

  if settings is None or settings.id_export_gsheet is None:
    raise InvalidArgument(_t("settings.gsheet.invalid.notconfigured"))

  gc = pygsheets.authorize(custom_credentials=get_creds())
  full_sheet = gc.open_by_key(settings.id_export_gsheet)
  
  characters_table = await create_characters_table(sess, str(guild.id))
  chr_worksheet = create_worksheet(full_sheet, "gci_characters", characters_table)
  loots_table = await create_loot_table(sess, str(guild.id))
  lts_worksheet = create_worksheet(full_sheet, "gci_loots", loots_table)

  # parse prio
  prio_parser = PrioParser(full_sheet)
  char_prio_sheet, class_prio_sheet = await generate_prio_sheets(sess, client, gc, full_sheet, guild, prio_parser._item_prio, prio_parser._role2name, for_event=for_event)

  return chr_worksheet, lts_worksheet, char_prio_sheet, class_prio_sheet, prio_parser