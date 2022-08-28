import pygsheets
from pygsheets import Spreadsheet, Worksheet
from discord import InvalidArgument
from sqlalchemy import select
from gsheet_helpers import get_creds
from models import Character, GuildSettings, Loot
from pycord18n.extension import _ as _t


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

  worksheet.insert_rows(0, len(table), table) 

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

