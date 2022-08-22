# environment variables
import os
from discord import Intents
import dotenv
import logging
import logging.config
from gci import GuildClockInBot
from lang.util import build_i18n, get_db_locale

if __name__ == "__main__":
  dotenv.load_dotenv()
  logging.config.fileConfig('./logging.conf')
  
  # logging
  level = os.getenv("LOG_LEVEL", "").upper()
  if level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    logging.getLogger().setLevel(level)  # only override default logger 

  # localization
  i18n = build_i18n("./lang")
  
  # bot
  intents = Intents.default()
  intents.members = True

  bot = GuildClockInBot(intents=intents)
  i18n.init_bot(bot, get_locale_func=get_db_locale)

  bot.run(os.getenv("BOT_TOKEN"))

  