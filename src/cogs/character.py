
import discord
from discord import InvalidArgument, Option, SlashCommandOptionType, guild_only
from discord.ext import commands

from db_util import add_character


class CharacterCog(commands.Cog):
  def __init__(self, bot): 
    self.bot = bot

  character_group = discord.SlashCommandGroup("character", "Character management")

  def get_applied_user_id(self, ctx, for_user, user_id):
    """return the id to which the query should be applied"""
    if for_user is None:
      return user_id

    if user_id != for_user.id and not ctx.author.guild_permissions.administrator:
      ctx.respond(f"Cannot add a character for another user than yourself.")
      raise InvalidArgument("cannot execute this command on behalf of another user")

    return str(for_user.id)

  @character_group.command()
  @guild_only()
  async def add(self, ctx, name: str, is_main: bool = False, for_user: discord.Member = None):
    """
    name: str
      Character name (case sensitive)
    is_main: bool
      If this character is the main character for the player. First character will always be set as main whatever the value of the parameter. 
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = self.get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session() as sess:
          async with sess.begin() as conn:
            created, character = await add_character(sess, user_id, guild_id, name, is_main=is_main)
            if created:
              await ctx.respond(f"The new character '{name}' was added (main: {character.is_main}).")
            else:
              await ctx.respond(f"Cannot add a character. The character '{name}' already exists.")
    
    except InvalidArgument as e:
      await ctx.respond(f"Cannot add a character for another user than yourself.")

  
  

def setup(bot):
  bot.add_cog(CharacterCog(bot))