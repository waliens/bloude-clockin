from abc import abstractmethod
from db_util.priorities import PrioTierEnum
from models import Attendance, Character, Raid, Loot
from db_util.wow_data import RaidSizeEnum
from sqlalchemy import select, update
from sqlalchemy.util import immutabledict


class AbstrackDKPSystem(object):
  @abstractmethod 
  def get_raid_points(self, attendance: Attendance):
    pass

  @abstractmethod
  def get_loot_points(self, loot: Loot, priority: PrioTierEnum):
    pass


class DefaultDKPSystem(AbstrackDKPSystem):
  def get_loot_points(self, loot: Loot, priority: PrioTierEnum):
    if not loot.in_dkp:
      return 0
    return {
      PrioTierEnum.IS_BIS: -5,
      PrioTierEnum.IS_ALMOST_BIS: -4,
      PrioTierEnum.IS_AVERAGE: -2,
      PrioTierEnum.IS_A_UP: -1
    }.get(priority, 0)

  def get_raid_points(self, attendance: Attendance):
    if attendance.is_guild_event:
      return 3
    else:
      return 5


async def compute_dkp_score(sess, character: Character, priorities: dict, dkp_system: AbstrackDKPSystem=None):
  if dkp_system is None:
    dkp_system = DefaultDKPSystem()
  
  # add from loots
  dkp_loots_query = select(Loot).where(Loot.id_character == character.id, Loot.in_dkp == True)
  dkp_loots_results = await sess.execute(dkp_loots_query)
  dkp_loots = dkp_loots_results.scalars().all()

  character_role = (character.character_class, character.role, character.spec) 

  dkp = 0
  for loot in dkp_loots:
    if loot.id_item not in priorities:
      continue 
    priority_list = priorities[loot.id_item].priority_list
    tier = priority_list.get_priority_tier(character_role)
    dkp += dkp_system.get_loot_points(loot, tier)

  # add from attendance
  dkp_attendances_query = select(Attendance).where(Attendance.id_character == character.id, Attendance.in_dkp == True)
  dkp_attendances_results = await sess.execute(dkp_attendances_query)
  dkp_attendances = dkp_attendances_results.scalars().all()

  for attendance in dkp_attendances:
    dkp += dkp_system.get_raid_points(attendance)

  return dkp

async def reset_dkp(sess, guild_id: int):
  character_select = select(Character.id).where(Character.id_guild == guild_id)
  update_attendances = update(Attendance).where(Attendance.id_character.in_(character_select)).values(in_dkp=False)
  update_loots = update(Loot).where(Loot.id_character.in_(character_select)).values(in_dkp=False)

  await sess.execute(update_attendances, execution_options=immutabledict({"synchronize_session": 'fetch'}))
  await sess.execute(update_loots, execution_options=immutabledict({"synchronize_session": 'fetch'}))