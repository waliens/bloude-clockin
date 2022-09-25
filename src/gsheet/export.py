import pygsheets

from collections import defaultdict
from pygsheets import Spreadsheet, Worksheet
from discord import InvalidArgument
from sqlalchemy import select
from db_util.dkp import compute_dkp_score
from db_util.priorities import PrioTierEnum, generate_prio_str_for_item
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
      loot.count,
      (loot.created_at if loot.updated_at is None else loot.updated_at).strftime('%d/%m/%Y %H:%M'),
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


async def generate_character_prio_sheet(sess, sheet, id_guild, items: dict, role2name: dict):
  """
  Parameters
  ----------
  sheet: pygsheets.SpreadSheet
    The worksheet will be generated/replaced here
  id_guild: [int|str]
    Guild identifierµ
  items: Mapping[int,ItemWithPriority]
  role2name: Mapping[tuple,str]
    Maps role tuples with its str name 
  """
  # read main characters list
  query = select(Character).where(Character.is_main == True, Character.id_guild == id_guild)
  results = await sess.execute(query)
  characters = results.scalars().all()
  char_dict = defaultdict(list)
  for char in characters:
    char_dkp = await compute_dkp_score(sess, char, items)
    char_dict[(char.character_class, char.role, char.spec)].append((char, char_dkp))

  # generate sheet table 
  sheet_table = list()
  sheet_table.append([
    _t("prio.gsheet.col.id"), 
    _t("prio.gsheet.col.name"), 
    _t("prio.gsheet.col.bis"), 
    _t("prio.gsheet.col.almost_bis"), 
    _t("prio.gsheet.col.average"), 
    _t("prio.gsheet.col.is_up")
  ])
  
  for item_id, item_with_priority in items.items():
    item = await sess.get(Item, item_id)
    if item is None:
      continue 
    prio_dict = await generate_prio_str_for_item(sess, id_guild, item_with_priority, role2name, char_dict)
    if len(prio_dict) == 0:
      continue
    item_descriptor = [item.id, localized_attr(item, 'name')] + [prio_dict.get(t, " ") for t in PrioTierEnum.useful_tiers()]
    sheet_table.append(item_descriptor)
  
  create_worksheet(sheet, name="gci_prio", table=sheet_table)
