import logging
import os
from discord import PartialEmoji, RawReactionActionEvent
import discord
from discord.ext import commands
from sqlalchemy import select
from database import init_db
from models import GuildCharter

class BloudeClockInBot(commands.Bot):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
  
    cog_exts = [
      "hello", 
      "character",
      "attendance",
      "loot",
      "guild_info"
    ]

    for cog_ext in cog_exts:
      cog_full_ext = f"cogs.{cog_ext}"
      result = self.load_extension(cog_full_ext)
      if isinstance(result[cog_full_ext], bool):
        logging.getLogger().info("loading '{}': successful".format(cog_full_ext))
      else:
        logging.getLogger().error("loading '{}': {}".format(cog_full_ext, str(result[cog_full_ext])))
        
    self._db_session_class = None
    self._db_engine = None
    self._db_session = None

  @property
  def db_session_class(self):
    return self._db_session_class

  @property
  def db_engine(self):
    return self._db_engine

  @property
  def db_session(self):
    return self._db_session
  
  async def on_ready(self):
    logging.getLogger().info("Bot `{}` is ready.".format(self.bot_classname))

  async def on_connect(self):
    await self._connect_db()
    logging.getLogger().info("Bot `{}` is connected.".format(self.bot_classname))

  async def on_disconnect(self):
    # await self._disconnect_db()
    logging.getLogger().info("Bot `{}` is disconnected.".format(self.bot_classname))

  async def on_resume(self):
    await self._connect_db()
    logging.getLogger().info("Bot `{}` resumed.".format(self.bot_classname))

  async def _disconnect_db(self):
    await self._do_disconnect_db()
    logging.getLogger().info("Bot `{}` disconnected from the database.".format(self.bot_classname))

  async def _do_disconnect_db(self):
    if self._db_session is not None:
      self._db_session.close()
    if self._db_engine is not None:
      await self._db_engine.dispose()

    self._db_session = None
    self._db_engine = None
    self._db_session_class = None

  async def _connect_db(self):
    await self._do_disconnect_db()
    self._db_session_class, self._db_engine = await init_db()
    self._db_session = self._db_session_class()
    logging.getLogger().info("Bot `{}` successfully connected to the database.".format(self.bot_classname))

  @property
  def bot_classname(self):
    return self.__class__.__name__

  async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
    """Watch for reactions on published charters."""
    guild = self.get_guild(payload.guild_id)
    if guild is None:
        return
    
    sess = self._db_session
    async with sess.begin():
      guild_id = str(guild.id)
      result = await sess.execute(select(GuildCharter).where(GuildCharter.id_guild == guild_id))
      charter = result.unique().scalars().one_or_none()
      sign_emoji = PartialEmoji(name=charter.sign_emoji)
      if charter is None or charter.id_sign_message is None or \
          charter.id_sign_message != str(payload.message_id) or payload.emoji != sign_emoji:
        return

      role = guild.get_role(int(charter.id_sign_role))
      if role is None: # role does not exists
        return 
      
      try:
        await payload.member.add_roles(role) 
      except discord.HTTPException as e:
        logging.getLogger().error(f"cannot add reaction role: {str(e)}")

  async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
    guild = self.get_guild(payload.guild_id)
    if guild is None:
      return
    sess = self._db_session
    async with sess.begin():
      guild_id = str(guild.id)
      result = await sess.execute(select(GuildCharter).where(GuildCharter.id_guild == guild_id))
      charter = result.unique().scalars().one_or_none()
      sign_emoji = PartialEmoji(name=charter.sign_emoji)

      if charter is None or charter.id_sign_message is None or \
          charter.id_sign_message != str(payload.message_id) or payload.emoji != sign_emoji:
        return
      
      role = guild.get_role(int(charter.id_sign_role))
      member = guild.get_member(payload.user_id)
      if role is None or member is None: # role does not exists
        return 

      try:
        await member.remove_roles(role) 
      except discord.HTTPException as e:
        logging.getLogger().error(f"cannot remove reaction role: {str(e)}")
    
      
