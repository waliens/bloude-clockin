
import logging
import discord
from discord import InvalidArgument, Option, SlashCommandOptionType, guild_only, slash_command
from discord.ext import commands

from db_util.character import add_character, update_character, delete_character


class CharacterCog(commands.Cog):
  def __init__(self, bot): 
    self.bot = bot

  character_group = discord.SlashCommandGroup("character", "Character management")

  @character_group.command()
  @guild_only()
  async def add(self, ctx, name: str, is_main: bool = False, for_user: discord.Member = None):
    """Add a new character
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = self._get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session() as sess:
        async with sess.begin():
          character = await add_character(sess, user_id, guild_id, name, is_main=is_main)
          await ctx.respond(f"The new character '{character.name}' was added (main: {character.is_main}).")
  
    except InvalidArgument as e:
      await ctx.respond(f"Cannot add a character: {str(e)}")

  @character_group.command()
  @guild_only()
  async def update(self, ctx, name: str, new_name: str = None, is_main: bool = None, for_user: discord.Member = None):
    """Update a character (by name)
    """
    try:
      if is_main is None and new_name is None:
        raise InvalidArgument("nothing to do, change either the name or the main status at least")

      guild_id = str(ctx.guild_id)
      user_id = self._get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session() as sess:
        async with sess.begin():
          character = await update_character(sess, user_id, guild_id, name, new_name, is_main)
          await ctx.respond(f"Update successful, the character is now named '{character.name}' (main: {character.is_main}).")
    
    except InvalidArgument as e:
      await ctx.respond(f"Cannot update a character: {str(e)}")

  @character_group.command()
  @guild_only()
  async def delete(self, ctx, name: str, for_user: discord.Member = None):
    """Delete a character
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = self._get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session() as sess:
        async with sess.begin():
          await delete_character(sess, user_id, guild_id, name)
          await ctx.respond(f"The character was sucessfully deleted, or did not exist.")
    
    except InvalidArgument as e:
      await ctx.respond(f"Cannot delete a character: {str(e)}")

  def _get_applied_user_id(self, ctx, for_user, user_id):
    """return the id to which the query should be applied"""
    if for_user is None:
      return user_id

    if user_id != for_user.id and not ctx.author.guild_permissions.administrator:
      raise InvalidArgument("you do not have the permissions to execute this command on behalf of another user")

    return str(for_user.id)
  
  @commands.Cog.listener()
  async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    logging.getLogger().error(str(error))
    raise error


  

def setup(bot):
  bot.add_cog(CharacterCog(bot))