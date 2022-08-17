# environment variables
import os
from discord import Intents
import dotenv
import logging
import logging.config
from bci import BloudeClockInBot

if __name__ == "__main__":
  dotenv.load_dotenv()
  logging.config.fileConfig('./logging.conf')
  
  level = os.getenv("LOG_LEVEL", "").upper()
  if level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
    logging.getLogger().setLevel(level)  # only override default logger 
  
  # bot
  intents = Intents.default()
  intents.members = True

  bot = BloudeClockInBot(intents=intents)
  bot.run(os.getenv("BOT_TOKEN"))
