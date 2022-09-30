import pygsheets

from collections import defaultdict
from pygsheets import Spreadsheet, Worksheet, Cell, DataRange
from discord import InvalidArgument
from sqlalchemy import select
from db_util.dkp import compute_dkp_score
from db_util.priorities import PrioTierEnum, generate_prio_str_for_item
from db_util.wow_data import ItemInventoryTypeEnum
from gsheet_helpers import get_creds
from models import Character, GuildSettings, Item, Loot
from pycord18n.extension import _ as _t
from lang.util import localized_attr


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
      character.is_main,
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


async def export_in_worksheets(sess, guild_id):
  settings = await sess.get(GuildSettings, guild_id)

  if settings is None or settings.id_export_gsheet is None:
    raise InvalidArgument(_t("settings.gsheet.invalid.notconfigured"))

  gc = pygsheets.authorize(custom_credentials=get_creds())
  full_sheet = gc.open_by_key(settings.id_export_gsheet)
  
  characters_table = await create_characters_table(sess, guild_id)
  chr_worksheet = create_worksheet(full_sheet, "gci_characters", characters_table)
  loots_table = await create_loot_table(sess, guild_id)
  lts_worksheet = create_worksheet(full_sheet, "gci_loots", loots_table)

  return chr_worksheet, lts_worksheet


async def generate_prio_sheets(sess, sheet, id_guild, priorities: dict, role2name: dict, per_class=False):
  """
  Parameters
  ----------
  sheet: pygsheets.SpreadSheet
    The worksheet will be generated/replaced here
  id_guild: [int|str]
    Guild identifierµ
  priorities: Mapping[int,ItemWithPriority]
  role2name: Mapping[tuple,str]
    Maps role tuples with its str name 
  """
  # read main characters list
  query = select(Character).where(Character.is_main == True, Character.id_guild == id_guild)
  results = await sess.execute(query)

  characters = results.scalars().all()
  char_dict = defaultdict(list)
  for char in characters:
    char_dkp = await compute_dkp_score(sess, char, priorities)
    char_dict[(char.character_class, char.role, char.spec)].append((char, char_dkp))

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
  
  slot_header_cell_merges = list()
  for slot, item_ids in per_slot.items():
    current_row = len(per_class_sheet_table) + 1
    slot_header_cell_merges.append(current_row)

    if slot is not None:
      per_class_sheet_table.append([slot.name_hr])
      per_char_sheet_table.append([slot.name_hr])
    else:
      per_class_sheet_table.append([ItemInventoryTypeEnum.NON_EQUIPABLE.name_hr])
      per_char_sheet_table.append([ItemInventoryTypeEnum.NON_EQUIPABLE.name_hr])

    for item_id in item_ids:
      item = item_index[item_id]
      row_header = [item.id, localized_attr(item, 'name'), item.metadata_["ItemLevel"]]
      # per_class
      per_class_prio_dict = await generate_prio_str_for_item(sess, id_guild, priorities[item_id], role2name)
      per_class_sheet_table.append(row_header + [per_class_prio_dict.get(t, " ") for t in PrioTierEnum.useful_tiers()])
      per_char_prio_dict = await generate_prio_str_for_item(sess, id_guild, priorities[item_id], role2name, char_dict)
      per_char_sheet_table.append(row_header + [per_char_prio_dict.get(t, " ") for t in PrioTierEnum.useful_tiers()])

  # actually generate the sheet
  for sheet_name, sheet_table in [("gci_prio", per_char_sheet_table), ("gci_prio_class", per_class_sheet_table)]: 
    wks = create_worksheet(sheet, name=sheet_name, table=sheet_table)

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
    