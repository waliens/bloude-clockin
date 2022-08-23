import os
import csv

from collections import defaultdict
from models import GuildSettings
from pycord18n.extension import I18nExtension, Language


def add_lang_entry(langs: dict, key: str, value: str, strict: bool=False):
  """
  Add a lang key:value entry in the langs dictionary. 
  
  Parameters
  ----------
  langs: dict
    Language dictionary
  key: str
    The language key
  value: str
    The language string
  strict: bool
    True to raise a ValueError exception if a key is replaced.
  """
  curr_dict = langs
  key_items = key.split(".")

  for key_item in key_items[:-1]:
    if key_item not in curr_dict:
      curr_dict[key_item] = dict()
    curr_dict = curr_dict[key_item]

  last_key_item = key_items[-1]
  if last_key_item in curr_dict and strict:
    raise ValueError(f"the language key '{key}' is already in the dictionary with value '{value}'.")
  if last_key_item in curr_dict and not isinstance(curr_dict[last_key_item], str):
    raise ValueError(f"the language key '{key}' is already in the dictionary but does not map a string.")
  
  curr_dict[last_key_item] = value


def read_lang(directory: str, strict: bool=False):
  with open(os.path.join(directory, "lang.csv"), "r", encoding="utf8") as file:
    reader = csv.reader(
      file, 
      delimiter=",", 
      doublequote=False, 
      quotechar='"', 
      escapechar='\\', 
      lineterminator=os.linesep, 
      quoting=csv.QUOTE_MINIMAL
    )
    header = next(reader)
    
    languages = header[1:]
    lang_dict = defaultdict(dict)

    for row in reader:
      key = row[0]
      for i, lang_string in enumerate(row[1:]):
        add_lang_entry(lang_dict[languages[i]], key, lang_string, strict=strict)

  return lang_dict
      

def build_i18n(directory: str):
  """Read supported languages from csv file and initialize i18n extension"""
  langs = read_lang(directory, strict=True)

  # # # 
  # TODO: config file
  supported_languages = [("English", "en"), ("Français", "fr")]
  # # #

  languages = list()
  for lang_name, lang_key in supported_languages:
    if lang_key not in langs:
      raise ValueError(f"language '{lang_key}' missing in lang file") 
    languages.append(Language(lang_name, lang_key, langs[lang_key]))

  return I18nExtension(languages, fallback=GuildSettings.DEFAULT_LOCALE)
  

async def get_db_locale(ctx):
  if ctx.guild is None:
    return None
  guild_id = str(ctx.guild.id)

  async with ctx.bot.db_session_class() as sess:
    async with sess.begin():
      settings = await sess.get(GuildSettings, guild_id)
      if settings is None:
        return None
      else: 
        return settings.locale


def localized_attr(obj, attr_name):
  locale = I18nExtension.default_i18n_instance.get_current_locale()
  try:
    return getattr(obj, attr_name + "_" + locale)
  except AttributeError:
    return getattr(obj, attr_name)
