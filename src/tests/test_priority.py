from unittest import TestCase
from item_priorities.priorities import PriorityList, PrioTierEnum
from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum

PALRET = (ClassEnum.PALADIN, RoleEnum.MELEE_DPS, None)
SPELLHANCE = (ClassEnum.SHAMAN, RoleEnum.MELEE_DPS, SpecEnum.SHAMAN_SPELLHANCE)

class TestPriorityList(TestCase):
  def testEmptyList(self):
    plist = PriorityList([])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_USELESS)
    self.assertFalse(plist.has_roles())
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))
    plist = PriorityList([None, ">>", None, ">>", None, ">>", None, ">>", None, ">>", None, ">>", None])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_USELESS)
    self.assertFalse(plist.has_roles())
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))
  
  def testOneItemBisList(self):
    plist = PriorityList([PALRET])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_BIS)
    self.assertTrue(plist.has_roles())
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))

  def testOneItemAlmostBisList(self):
    plist = PriorityList([None, ">>", PALRET, ">>"])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_ALMOST_BIS)
    self.assertTrue(plist.has_roles())
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))

  def testOneItemAverageList(self):
    plist = PriorityList([None, ">>", None, ">>", PALRET])
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_AVERAGE)
    self.assertTrue(plist.has_roles())
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))

  def testOneItemIsUpList(self):
    plist = PriorityList([None, ">>", None, ">>", None, ">>", PALRET])
    self.assertTrue(plist.has_roles())
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_A_UP)
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_A_UP))

  def testTwoClasses(self):
    plist = PriorityList([SPELLHANCE, ">>", PALRET, ">>", None, ">>", None])
    self.assertGreater(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertEqual(plist.get_priority_tier(SPELLHANCE), PrioTierEnum.IS_BIS)
    self.assertEqual(plist.get_priority_tier(PALRET), PrioTierEnum.IS_ALMOST_BIS)
    self.assertTrue(plist.is_better(SPELLHANCE, PALRET))
    self.assertTrue(plist.has_roles())
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_BIS))
    self.assertTrue(plist.tier_has_roles(PrioTierEnum.IS_ALMOST_BIS))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_AVERAGE))
    self.assertFalse(plist.tier_has_roles(PrioTierEnum.IS_A_UP))
    plist = PriorityList([SPELLHANCE, ">", PALRET, ">>", None, ">>", None])
    self.assertGreater(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertTrue(plist.is_better(SPELLHANCE, PALRET))
    plist = PriorityList([SPELLHANCE, "~", PALRET, ">>", None, ">>", None])
    self.assertEqual(plist.cmp(SPELLHANCE, PALRET), 0)
    self.assertFalse(plist.is_better(SPELLHANCE, PALRET))