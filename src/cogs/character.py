import datetime
import pprint
import discord
from sqlalchemy import and_, select, update
from discord.ext import commands

from models import Character


class CharacterCog(commands.Cog):
  def __init__(self, bot): 
    self.bot = bot

  character_group = discord.SlashCommandGroup("character", "Character management")

  @character_group.command()
  async def add(self, ctx, name: str, is_main: bool = False):
    """
    name: str
      Character name (case sensitive)
    is_main: bool
      If this character is the main character for the player. First character will always be set as main whatever the value of the parameter. 
    """
    guild_id = str(ctx.guild_id)
    user_id = str(ctx.user.id)
    async with self.bot.db_session() as sess:
        async with sess.begin() as conn:
          where_clause = [Character.id_guild == guild_id, Character.id_user == user_id]
          query = select(Character).where(*where_clause)
          user_characters = (await sess.execute(query)).mappings().all()
          if len(user_characters) == 0 or len([c for c in user_characters if c['Character'].name == name]) == 0:
            new_character = Character(
              name=name, 
              id_guild=guild_id, 
              id_user=user_id, 
              is_main=len(user_characters) == 0 or is_main, 
              created_at=datetime.datetime.now()
            )

            if is_main:
              await sess.execute(update(Character).where(*where_clause).values(is_main=False))
            sess.add(new_character)
            await sess.commit()
            await ctx.respond(f"The new character '{name}' was added (main: {len(user_characters) == 0 or is_main}).")
          else:
            await ctx.respond(f"Cannot add a character. The character '{name}' already exists.")
            

def setup(bot):
  bot.add_cog(CharacterCog(bot))