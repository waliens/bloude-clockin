from unittest import TestCase

from cogs.util import parse_loots_str, validate_character_name
from lang.util import build_i18n
from discord import InvalidArgument 


class CogsUtilTests(TestCase):
  def setUp(self):
    _ = build_i18n("./src/lang")
    
  def testParseLootsStrEmptyList(self):
    empty_list = ""
    res = parse_loots_str(empty_list)
    self.assertIsInstance(res, dict)
  
  def testParseLootsStr(self):
    l = "Arthas:40800,39865;Lutherqt:25006"
    res = parse_loots_str(l)
    self.assertEqual(len(res), 2)
    self.assertIn("Arthas", res)
    self.assertIn("Lutherqt", res)
    self.assertListEqual(res["Arthas"], [40800, 39865])
    self.assertListEqual(res["Lutherqt"], [25006])

  def testParseLootsStrInvalid(self):
    l = "Art:"
    with self.assertRaises(InvalidArgument):
      _ = parse_loots_str(l)
  
  def testValidateCharacterName(self):
    self.assertEqual(validate_character_name("name"), "Name")
    self.assertEqual(validate_character_name("Name"), "Name")
    self.assertEqual(validate_character_name("NaMe"), "Name")
    
    with self.assertRaises(InvalidArgument):
      validate_character_name("name aa")