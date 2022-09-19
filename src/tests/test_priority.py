from unittest import TestCase
from item_priorities.priorities import PriorityList, PrioTierEnum
from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum

PALRET = (ClassEnum.PALADIN, RoleEnum.MELEE_DPS, None)
SPELLHANCE = (ClassEnum.SHAMAN, RoleEnum.MELEE_DPS, SpecEnum.SHAMAN_SPELLHANCE)

class TestPriorityList(TestCase):
  def testEmptyList(self):
    plist = PriorityList([])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_USELESS)
    plist = PriorityList([None, ">>", None, ">>", None, ">>", None, ">>", None, ">>", None, ">>", None])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_USELESS)
  
  def testOneItemBisList(self):
    plist = PriorityList([PALRET])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_BIS)

  def testOneItemAlmostBisList(self):
    plist = PriorityList([None, ">>", PALRET, ">>"])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_ALMOST_BIS)

  def testOneItemAverageList(self):
    plist = PriorityList([None, ">>", None, ">>", PALRET])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_AVERAGE)

  def testOneItemIsUpList(self):
    plist = PriorityList([None, ">>", None, ">>", None, ">>", PALRET])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_A_UP)

  def testTwoClasses(self):
    plist = PriorityList([SPELLHANCE, ">>", PALRET, ">>", None, ">>", None])
    self.assertGreater(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertEqual(plist.get_priority_tier(SPELLHANCE), PrioTierEnum.IS_BIS)
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_ALMOST_BIS)
    self.assertTrue(plist.is_better(SPELLHANCE, PALRET))
    plist = PriorityList([SPELLHANCE, ">", PALRET, ">>", None, ">>", None])
    self.assertGreater(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertTrue(plist.is_better(SPELLHANCE, PALRET))
    plist = PriorityList([SPELLHANCE, "~", PALRET, ">>", None, ">>", None])
    self.assertEqual(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertFalse(plist.is_better(SPELLHANCE, PALRET))