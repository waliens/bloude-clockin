
import datetime
import re
from discord import InvalidArgument

from pycord18n.extension import _ as _t


def default_if_none(v, d=None):
  return d if v is None else v


def get_applied_user_id(ctx, for_user, user_id, requires_admin=True):
  """return the id to which the query should be applied"""
  if for_user is None:
    return user_id

  if user_id != str(for_user.id) and (requires_admin and not ctx.author.guild_permissions.administrator):
    raise InvalidArgument(_t("general.invalid.onbehalf"))

  return str(for_user.id)


def parse_date(date_str, default=None):
  try:
    if date_str is None:
      return default
    return datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
  except ValueError:
    raise InvalidArgument(_t("general.invalid.date"))


def parse_datetime(datetime_str, default=None):
  try:
    if datetime_str is None:
      return default
    return datetime.datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
  except ValueError:
    raise InvalidArgument(_t("general.invalid.datetime"))


def validate_character_name(s):
  if re.search(r"\s+", s) is not None:
    raise InvalidArgument(_t("character.invalid.character_name"))
  return s.lower().capitalize()


def parse_loots_str(loots: str):
  if len(loots.strip()) == 0:
    return {}

  pattern = r"^(?:[^:;]+:(?:[0-9]+)(?:,[0-9]+)*)(?:;[^:;]+:(?:[0-9]+)(?:,[0-9]+)*)*$"
      
  if re.match(pattern, loots) is None:
    raise InvalidArgument(_t("loot.invalid.bulk_str"))
  
  return {
    validate_character_name(char_list.split(":")[0].strip()): list(map(int, char_list.split(":")[1].split(","))) 
    for char_list in loots.split(";")
  }


def parse_identifiers_str(l):
  """check a comma separated list of integer identifiers"""
  if re.match("^\s*[0-9]+(\s*,\s*[0-9]+)*\s*$", l) is None:
    raise InvalidArgument(_t("general.invalid.id_list"))
  return [int(v.strip()) for v in l.split(",")]