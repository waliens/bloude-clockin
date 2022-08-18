import re
from enum import Enum


def enum_names(enum_type):
  return [v.name for v in enum_type]


class HumanReadableEnum(Enum): # TODO i18n
  @property
  def name_hr(self):
    return re.sub(r"[\s_]+", " ", self.name).lower().capitalize()



class ItemClassEnum(HumanReadableEnum):
  CONSUMABLE = 0
  CONTAINER = 1
  WEAPON = 2
  GEM = 3
  ARMOR = 4
  REAGENT = 5
  PROJECTILE = 6
  TRADE_GOODS = 7
  GENERIC = 8
  RECIPE = 9
  MONEY = 10
  QUIVER = 11
  QUEST = 12
  KEY = 13
  PERMANENT = 14
  MISCELLANEOUS = 15
  GLYPH = 16
  
  @property
  def name_hr(self):
    base_name = super().name_hr
    if self == self.GENERIC or self == self.MONEY or self == self.PERMANENT:
      base_name += " (OBSOLETE)"
    return base_name



class ItemQualityEnum(HumanReadableEnum):
  POOR = 0
  COMMON = 1
  UNCOMMON = 2
  RARE = 3
  EPIC = 4
  LEGENDARY = 5
  ARTIFACT = 6
  BIND_TO_ACCOUNT = 7

  @property
  def color(self):
    if self == self.POOR:
      return "Grey"
    elif self == self.COMMON:
      return "White"
    elif self == self.UNCOMMON:
      return "Green"
    elif self == self.RARE:
      return "Blue"
    elif self == self.EPIC:
      return "Purple"
    elif self == self.LEGENDARY:
      return "Orange"
    elif self == self.ARTIFACT:
      return "Red"
    elif self == self.BIND_TO_ACCOUNT:
      return "Gold"
    else:
      raise ValueError("unknown quality")


class InventorySlotEnum():
  AMMO = 0	
  HEAD = 1	
  NECK = 2	
  SHOULDER = 3	
  BODY = 4	
  CHEST = 5	
  WAIST = 6	
  LEGS = 7	
  FEET = 8	
  WRIST = 9	
  HAND = 10	
  FINGER1 = 11	
  FINGER2 = 12	
  TRINKET1 = 13	
  TRINKET2 = 14	
  BACK = 15	
  MAINHAND = 16	
  OFFHAND = 17	
  RANGED = 18	
  TABARD = 19	
  

class ItemInventoryEnum(HumanReadableEnum):
  NON_EQUIPABLE = 0
  HEAD = 1
  NECK = 2
  SHOULDER = 3
  SHIRT = 4
  CHEST = 5
  WAIST = 6
  LEGS = 7
  FEET = 8
  WRISTS = 9
  HANDS = 10
  FINGER = 11
  TRINKET = 12
  WEAPON = 13
  SHIELD = 14
  RANGED = 15
  BACK = 16
  TWO_HAND = 17
  BAG = 18
  TABARD = 19
  ROBE = 20
  MAIN_HAND = 21
  OFF_HAND = 22
  HOLDABLE = 23
  AMMO = 24
  THROWN = 25
  RANGED_RIGHT = 26
  QUIVER = 27
  RELIC = 28

  @property
  def name_hr(self):
    base_name = super().name_hr
    if self == self.RANGED:
      base_name += " (Bows)"
    elif self == self.HOLDABLE:
      base_name += " (Tome)"
    elif self == self.RANGED_RIGHT:
      base_name += " (Wands, Guns)"
    return base_name

  def get_slot(self):
    if self == self.HEAD:
      return InventorySlotEnum.HEAD
    elif self == self.NECK:
      return InventorySlotEnum.NECK
    elif self == self.SHOULDER:
      return InventorySlotEnum.SHOULDER
    elif self == self.SHIRT:
      return InventorySlotEnum.BODY
    elif self == self.CHEST:
      return InventorySlotEnum.CHEST
    elif self == self.WAIST:
      return InventorySlotEnum.WAIST
    elif self == self.LEGS:
      return InventorySlotEnum.LEGS
    elif self == self.FEET:
      return InventorySlotEnum.FEET
    elif self == self.WRISTS:
      return InventorySlotEnum.WRIST
    elif self == self.HANDS:
      return InventorySlotEnum.HAND
    elif self == self.FINGER:
      return InventorySlotEnum.FINGER1
    elif self == self.TRINKET:
      return InventorySlotEnum.TRINKET1
    elif self == self.WEAPON:
      return InventorySlotEnum.MAINHAND
    elif self == self.SHIELD:
      return InventorySlotEnum.OFFHAND
    elif self == self.RANGED:
      return InventorySlotEnum.RANGED
    elif self == self.BACK:
      return InventorySlotEnum.BACK
    elif self == self.TWO_HAND:
      return InventorySlotEnum.MAINHAND
    elif self == self.BAG:
      return None
    elif self == self.TABARD:
      return InventorySlotEnum.BODY
    elif self == self.ROBE:
      return InventorySlotEnum.BODY
    elif self == self.MAIN_HAND:
      return InventorySlotEnum.MAINHAND
    elif self == self.OFF_HAND:
      return InventorySlotEnum.OFFHAND
    elif self == self.HOLDABLE:
      return InventorySlotEnum.MAINHAND
    elif self == self.AMMO:
      return InventorySlotEnum.AMMO
    elif self == self.THROWN:
      return InventorySlotEnum.AMMO
    elif self == self.RANGED_RIGHT:
      return InventorySlotEnum.RANGED
    elif self == self.QUIVER:
      return None
    elif self == self.RELIC:
      return InventorySlotEnum.RANGED
    return None


class StatsEnum(HumanReadableEnum):
  MANA = 0
  HEALTH = 1
  AGILITY = 3
  STRENGTH = 4
  INTELLECT = 5
  SPIRIT = 6
  STAMINA = 7
  DEFENSE_SKILL_RATING = 12
  DODGE_RATING = 13
  PARRY_RATING = 14
  BLOCK_RATING = 15
  HIT_MELEE_RATING = 16
  HIT_RANGED_RATING = 17
  HIT_SPELL_RATING = 18
  CRIT_MELEE_RATING = 19
  CRIT_RANGED_RATING = 20
  CRIT_SPELL_RATING = 21
  HIT_TAKEN_MELEE_RATING = 22
  HIT_TAKEN_RANGED_RATING = 23
  HIT_TAKEN_SPELL_RATING = 24
  CRIT_TAKEN_MELEE_RATING = 25
  CRIT_TAKEN_RANGED_RATING = 26
  CRIT_TAKEN_SPELL_RATING = 27
  HASTE_MELEE_RATING = 28
  HASTE_RANGED_RATING = 29
  HASTE_SPELL_RATING = 30
  HIT_RATING = 31
  CRIT_RATING = 32
  HIT_TAKEN_RATING = 33
  CRIT_TAKEN_RATING = 34
  RESILIENCE_RATING = 35
  HASTE_RATING = 36
  EXPERTISE_RATING = 37
  ATTACK_POWER = 38
  RANGED_ATTACK_POWER = 39
  FERAL_ATTACK_POWER = 40
  SPELL_HEALING_DONE = 41
  SPELL_DAMAGE_DONE = 42
  MANA_REGENERATION = 43
  ARMOR_PENETRATION_RATING = 44
  SPELL_POWER = 45
  HEALTH_REGEN = 46
  SPELL_PENETRATION = 47
  BLOCK_VALUE = 48


class RoleEnum(HumanReadableEnum):
  TANK = 1
  HEALER = 2
  MELEE_DPS = 3
  RANGED_DPS = 4

  @property
  def name_hr(self):
    if self == self.MELEE_DPS:
      base_name = "Melee DPS"
    elif self == self.RANGED_DPS:
      base_name = "Ranged DPS"
    else: 
      base_name = super().name_hr
    return base_name


class ClassEnum(HumanReadableEnum):
  WARRIOR = 1
  PALADIN = 2
  HUNTER = 3
  ROGUE = 4
  PRIEST = 5
  DEATH_KNIGHT = 6
  SHAMAN = 7
  MAGE = 8
  WARLOCK = 9
  DRUID = 11

  def get_specs(self, role: RoleEnum):
    if self == self.ROGUE and role == RoleEnum.MELEE_DPS:
      return [SpecEnum.ROGUE_ASSA, SpecEnum.ROGUE_COMBAT]
    elif self == self.SHAMAN and role == RoleEnum.MELEE_DPS:
      return [SpecEnum.SHAMAN_ENHANCE, SpecEnum.SHAMAN_SPELLHANCE]
    elif self == self.WARLOCK and role == RoleEnum.RANGED_DPS:
      return [SpecEnum.WARLOCK_AFFLI, SpecEnum.WARLOCK_DEMONO]
    else:
      return []

  @staticmethod
  def get_all_specs_with_class():
    return {(c, s) for c in ClassEnum for s in c.get_specs()}


class SpecEnum(HumanReadableEnum):
  SHAMAN_ENHANCE = 1
  SHAMAN_SPELLHANCE = 2
  WARLOCK_AFFLI = 3
  WARLOCK_DEMONO = 4
  ROGUE_COMBAT = 5
  ROGUE_ASSA = 6

  @property
  def name_hr(self):
    if self == self.SHAMAN_ENHANCE:
      return "Enhance"
    elif self == self.SHAMAN_SPELLHANCE:
      return "Spellhance"
    elif self == self.WARLOCK_AFFLI:
      return "Affliction"
    elif self == self.WARLOCK_DEMONO:
      return "Demonology"
    elif self == self.ROGUE_COMBAT:
      return "Combat"
    elif self == self.ROGUE_ASSA:
      return "Assassination"
    else:
      return super().name_hr

  @property
  def character_class(self):
    if self == self.SHAMAN_ENHANCE:
      return ClassEnum.SHAMAN  
    elif self == self.SHAMAN_SPELLHANCE:
      return ClassEnum.SHAMAN
    elif self == self.WARLOCK_AFFLI:
      return ClassEnum.WARLOCK
    elif self == self.WARLOCK_DEMONO:
      return ClassEnum.WARLOCK
    elif self == self.ROGUE_COMBAT:
      return ClassEnum.ROGUE
    elif self == self.ROGUE_ASSA:
      return ClassEnum.ROGUE
    else:
      raise ValueError("unknown spec")

  @property
  def role(self):
    if self == self.SHAMAN_ENHANCE:
      return RoleEnum.MELEE_DPS  
    elif self == self.SHAMAN_SPELLHANCE:
      return RoleEnum.MELEE_DPS
    elif self == self.WARLOCK_AFFLI:
      return RoleEnum.RANGED_DPS
    elif self == self.WARLOCK_DEMONO:
      return RoleEnum.RANGED_DPS
    elif self == self.ROGUE_COMBAT:
      return RoleEnum.MELEE_DPS
    elif self == self.ROGUE_ASSA:
      return RoleEnum.MELEE_DPS
    else:
      raise ValueError("unknown spec")

  @staticmethod
  def has_spec(_class: ClassEnum, role: RoleEnum):
    return _class == ClassEnum.ROGUE or (_class == ClassEnum.SHAMAN and role == RoleEnum.MELEE_DPS) or (_class == ClassEnum.WARLOCK and role == RoleEnum.RANGED_DPS) 
  
  def is_valid_for_class_role(self, _class: ClassEnum, role: RoleEnum):
    return self.role == role and self.character_class == _class


class RaidSizeEnum(HumanReadableEnum):
  RAID10 = 1
  RAID25 = 2


def is_valid_class_role(chr_class: ClassEnum, role: RoleEnum):
  return (chr_class == ClassEnum.WARRIOR and role in {RoleEnum.TANK, RoleEnum.MELEE_DPS}) or \
    (chr_class == ClassEnum.PALADIN and role in {RoleEnum.TANK, RoleEnum.MELEE_DPS, RoleEnum.HEALER}) or \
    (chr_class == ClassEnum.HUNTER and role in {RoleEnum.RANGED_DPS}) or \
    (chr_class == ClassEnum.ROGUE and role in {RoleEnum.MELEE_DPS}) or \
    (chr_class == ClassEnum.PRIEST and role in {RoleEnum.RANGED_DPS, RoleEnum.HEALER}) or \
    (chr_class == ClassEnum.DEATH_KNIGHT and role in {RoleEnum.TANK, RoleEnum.MELEE_DPS}) or \
    (chr_class == ClassEnum.SHAMAN and role in {RoleEnum.MELEE_DPS, RoleEnum.RANGED_DPS, RoleEnum.HEALER}) or \
    (chr_class == ClassEnum.MAGE and role in {RoleEnum.RANGED_DPS}) or \
    (chr_class == ClassEnum.WARLOCK and role in {RoleEnum.RANGED_DPS}) or \
    (chr_class == ClassEnum.DRUID)
