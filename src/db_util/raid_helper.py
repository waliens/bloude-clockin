import asyncio
from collections import defaultdict
from datetime import datetime
import json
import requests
from discord import InvalidArgument
from db_util.character import get_user_characters
from db_util.wow_data import SpecEnum, ClassEnum, RoleEnum
from pycord18n.extension import _ as _t

def get_raid_helper_event(event_id: id):
  result = requests.get(f"https://raid-helper.dev/api/event/{event_id}")
  if result.status_code == 404:
    raise InvalidArgument(_t("attendance.raid_helper.invalid.notfound"))
  elif result.status_code == 403: 
    raise InvalidArgument(_t("attendance.raid_helper.invalid.forbidden"))
  elif result.status_code != 200:
    raise InvalidArgument(_t("attendance.raid_helper.invalid.http", error=result.status_code))
  return result.json()


def get_role(spec_name):
  return {
    "Frost": (ClassEnum.MAGE, RoleEnum.RANGED_DPS, None),
    "Fire": (ClassEnum.MAGE, RoleEnum.RANGED_DPS, None),
    "Arcane": (ClassEnum.MAGE, RoleEnum.RANGED_DPS, None),
    "Assassination": (ClassEnum.ROGUE, RoleEnum.MELEE_DPS, SpecEnum.ROGUE_ASSA),
    "Combat": (ClassEnum.ROGUE, RoleEnum.MELEE_DPS, SpecEnum.ROGUE_COMBAT),
    "Subtlety": (ClassEnum.ROGUE, RoleEnum.MELEE_DPS, None),
    "Protection": (ClassEnum.WARRIOR, RoleEnum.TANK, None),
    "Fury": (ClassEnum.WARRIOR, RoleEnum.MELEE_DPS, None),
    "Arms": (ClassEnum.WARRIOR, RoleEnum.MELEE_DPS, None),
    "Discipline": (ClassEnum.PRIEST, RoleEnum.HEALER, SpecEnum.PRIEST_DISC),
    "Holy": (ClassEnum.PRIEST, RoleEnum.HEALER, SpecEnum.PRIEST_HOLY),
    "Shadow": (ClassEnum.PRIEST, RoleEnum.RANGED_DPS, None),
    "Affliction": (ClassEnum.WARLOCK, RoleEnum.RANGED_DPS, SpecEnum.WARLOCK_AFFLI),
    "Demonology": (ClassEnum.WARLOCK, RoleEnum.RANGED_DPS, SpecEnum.WARLOCK_DEMONO),
    "Destruction": (ClassEnum.WARLOCK, RoleEnum.RANGED_DPS, None),
    "Beastmastery": (ClassEnum.HUNTER, RoleEnum.RANGED_DPS, None),
    "Marksman": (ClassEnum.HUNTER, RoleEnum.RANGED_DPS, None),
    "Marksmanship": (ClassEnum.HUNTER, RoleEnum.RANGED_DPS, None),
    "Survival": (ClassEnum.HUNTER, RoleEnum.RANGED_DPS, None),
    "Holy1": (ClassEnum.PALADIN, RoleEnum.HEALER, None),
    "Retribution": (ClassEnum.PALADIN, RoleEnum.MELEE_DPS, None),
    "Protection1": (ClassEnum.PALADIN, RoleEnum.TANK, None),
    "Blood_DPS": (ClassEnum.DEATH_KNIGHT, RoleEnum.MELEE_DPS, None),
    "Frost_DPS": (ClassEnum.DEATH_KNIGHT, RoleEnum.MELEE_DPS, SpecEnum.DK_FROST),
    "Unholy_DPS": (ClassEnum.DEATH_KNIGHT, RoleEnum.MELEE_DPS, SpecEnum.DK_UNHOLY),
    "Blood_Tank": (ClassEnum.DEATH_KNIGHT, RoleEnum.TANK, None),
    "Frost_Tank": (ClassEnum.DEATH_KNIGHT, RoleEnum.TANK, None),
    "Unholy_Tank": (ClassEnum.DEATH_KNIGHT, RoleEnum.TANK, None),
    "Restoration": (ClassEnum.DRUID, RoleEnum.HEALER, None),
    "Feral": (ClassEnum.DRUID, RoleEnum.MELEE_DPS, None),
    "Balance": (ClassEnum.DRUID, RoleEnum.RANGED_DPS, None),
    "Guardian": (ClassEnum.DRUID, RoleEnum.TANK, None),
    "Elemental": (ClassEnum.SHAMAN, RoleEnum.RANGED_DPS, None),
    "Restoration1": (ClassEnum.SHAMAN, RoleEnum.HEALER, None),
    "Enhancement": (ClassEnum.SHAMAN, RoleEnum.MELEE_DPS, None)
  }[spec_name]


async def extract_raid_helpers_data(sess, rh_event_id: int, guild_id):
  loop = asyncio.get_event_loop()
  rh_event_data = await loop.run_in_executor(None, get_raid_helper_event, rh_event_id)
   
  if rh_event_data.get("status", "success") == "failed":
    raise InvalidArgument(_t("attendance.raid_helper.invalid.notfound"))

  when = datetime.strptime(f"{rh_event_data['date']} {rh_event_data['time']}", "%d-%m-%Y %H:%M")

  registered = list()
  missing = list()
  for signup in rh_event_data["signups"]:
    if signup["role"] == "Absence" or signup["class"] == "Bench":
      continue

    characters = await get_user_characters(sess, id_guild=guild_id, id_user=int(signup["userid"]))
    parsed_role = get_role(signup["spec"])

    # find best match between raid helper class and spec data and actual characters from db
    # only class must match exactly (to handle double spec and specs unknown to raid helper)
    best_match = None
    best_match_extent = 0
    for character in characters:
      if character.character_class != parsed_role[0]:
        match_extent = 0
      elif character.role != parsed_role[1]:
        match_extent = 1
      elif character.spec != parsed_role[2]:
        if parsed_role[2] is None:
          match_extent = 2.5
        else: 
          match_extent = 2
      else:
        match_extent = 3
      
      if match_extent > 0 and match_extent > best_match_extent:
        best_match_extent = match_extent
        best_match = character
    
    if best_match is not None:
      registered.append(best_match)
    else:
      missing.append(signup["name"])

  return when, registered, missing
