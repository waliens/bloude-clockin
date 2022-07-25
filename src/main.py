# environment variables
import os
import dotenv
import asyncio
import logging
import logging.config
from bci import BloudeClockInBot

if __name__ == "__main__":
  dotenv.load_dotenv()
  # logging.config.fileConfig('./logging.conf')
  
  # level = os.getenv("LOG_LEVEL", "").upper()
  # if level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
  #   for name in logging.root.manager.loggerDict:
  #     logging.getLogger(name).setLevel(level)
  
  # bot
  bot = BloudeClockInBot()
  bot.run(os.getenv("BOT_TOKEN"))
