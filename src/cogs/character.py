
import logging
import os
import discord
from discord import InvalidArgument, Option, guild_only, slash_command
from discord.ext import commands
from sqlalchemy import select

from ui.character import SpecSelectionView

from .util import default_if_none, get_applied_user_id
from db_util.character import add_character, get_character, update_character, delete_character
from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum
from models import Character


class CharacterCog(commands.Cog):
  def __init__(self, bot): 
    self.bot = bot

  character_group = discord.SlashCommandGroup("character", "Character management")

  @character_group.command(description="Create a character")
  @guild_only()
  async def create(self, ctx, 
    name: str, 
    role: RoleEnum, 
    character_class: Option(ClassEnum, "class"),
    is_main: bool = False, 
    for_user: discord.Member = None
  ):
    """Add a new character
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          success_msg = "The new character '{name}' was added (main: {is_main})."
          if SpecEnum.has_spec(character_class, role):
            
            # callback for spec button click
            async def click_callback(spec: SpecEnum):
              async with self.bot.db_session_class() as sess:
                async with sess.begin():
                  character = await add_character(sess, user_id, guild_id, name, role, character_class, spec=spec, is_main=is_main)
                  return success_msg.format(name=character.name, is_main=character.is_main)

            view = SpecSelectionView(click_callback, character_class, role)
            await ctx.respond(view=view, ephemeral=True)
          else:
            character = await add_character(sess, user_id, guild_id, name, role, character_class, is_main=is_main)
            await ctx.respond(success_msg.format(name=character.name, is_main=character.is_main), ephemeral=True)
  
    except InvalidArgument as e:
      await ctx.respond(f"Cannot add a character: {str(e)}", ephemeral=True)

  @character_group.command(description="Update a character")
  @guild_only()
  async def update(self, ctx, 
    name: str, 
    new_name: str = None, 
    is_main: bool = None, 
    for_user: discord.Member = None, 
    role: Option(RoleEnum, description="If specified, will also trigger spec update when relevant") = None, 
    character_class: Option(ClassEnum, name="class", description="If specified, will also trigger spec update when relevant") = None
  ):
    """Update a character (by name)
    """
    try:
      if is_main is None and new_name is None and role is None and character_class is None:
        raise InvalidArgument("nothing to do, change either the name or the main status at least")

      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          old_character = await get_character(sess, guild_id, user_id, name)
          final_class = default_if_none(character_class, old_character.character_class)
          final_role = default_if_none(role, old_character.role)
          success_msg = "Update successful, the character is now named '{name}' (main: {is_main})."
          if (character_class is not None or role is not None) and SpecEnum.has_spec(final_class, final_role):

            # callback for spec button click
            async def click_callback(spec: SpecEnum):
              async with self.bot.db_session_class() as sess:
                async with sess.begin():
                  character = await update_character(sess, user_id, guild_id, name, new_name, is_main=is_main, role=role, spec=spec, character_class=character_class)
                  return success_msg.format(name=character.name, is_main=character.is_main)

            view = SpecSelectionView(click_callback, character_class, role)
            await ctx.respond(view=view, ephemeral=True)
          
          else:
            character = await update_character(sess, user_id, guild_id, name, new_name, is_main=is_main, role=role, character_class=character_class)
            await ctx.respond(success_msg.format(name=character.name, is_main=character.is_main), ephemeral=True)
    
    except InvalidArgument as e:
      await ctx.respond(f"Cannot update a character: {str(e)}", ephemeral=True)

  @character_group.command(description="Delete a character")
  @guild_only()
  async def delete(self, ctx, name: str, for_user: discord.Member = None):
    """Delete a character
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          await delete_character(sess, user_id, guild_id, name)
          await ctx.respond(f"The character was sucessfully deleted, or did not exist.", ephemeral=True)
    
    except InvalidArgument as e:
      await ctx.respond(f"Cannot delete a character: {str(e)}", ephemeral=True)

  @discord.slash_command(description="List of characters")
  @guild_only()
  async def characters(self, ctx, 
    for_user: Option(discord.Member, description="Display the list for the selected user (admin only).") = None, 
    public: Option(bool, description="To display the characters list publicly.") = False
  ):
    """List all characters in an embed
    """
    try:
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
    
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          characters = (await sess.execute(select(Character).where(
            Character.id_user == user_id,
            Character.id_guild == guild_id
          ).order_by(Character.is_main.desc()))).scalars().all()

          if len(characters) > 0:
            formatted = list()
            for c in characters:
              descriptor = ":" + {RoleEnum.HEALER: "ambulance", RoleEnum.MELEE_DPS: "crossed_swords", RoleEnum.RANGED_DPS: "bow_and_arrow", RoleEnum.TANK: "shield"}[c.role] + ":"
              descriptor += " "
              if c.is_main:
                descriptor += "**"
              descriptor +=  c.name
              if c.is_main:
                descriptor += "**"
              descriptor +=  f" ({c.character_class.name_hr}"
              if c.spec is not None:
                descriptor += f" {c.spec.name_hr.lower()}"
              descriptor += ")"
              formatted.append(descriptor)
            description = os.linesep.join(formatted)
          else:
            description = "No character registered."

          embed = discord.Embed(
            title="List of characters",
            description=description
          )

          await ctx.respond(embed=embed, ephemeral=not public)

    except InvalidArgument as e:
      await ctx.respond(f"Cannot list characters: {str(e)}", ephemeral=True)

  @commands.Cog.listener()
  async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    logging.getLogger().error(str(error))
    raise error


def setup(bot):
  bot.add_cog(CharacterCog(bot))