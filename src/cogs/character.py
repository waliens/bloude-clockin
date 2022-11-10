
import logging
import os
import discord
from discord import InvalidArgument, Option, guild_only
from discord.ext import commands
from sqlalchemy import select

from ui.character import CharacterListEmbed, SpecSelectionView

from .util import default_if_none, get_applied_user_id, validate_character_name
from db_util.character import add_character, get_character, update_character, delete_character
from db_util.wow_data import ClassEnum, MainStatusEnum, RoleEnum, SpecEnum
from models import Character

from pycord18n.extension import _ as _t


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
    main_status: Option(MainStatusEnum, description="Whether the character is a main or reroll.") = None, 
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None
  ):
    """Add a new character
    """
    try:
      name = validate_character_name(name)
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          if SpecEnum.has_spec(character_class, role):
            
            # callback for spec button click
            async def click_callback(spec: SpecEnum):
              async with self.bot.db_session_class() as sess:
                async with sess.begin():
                  character = await add_character(sess, user_id, guild_id, name, role, character_class, spec=spec, main_status=main_status)
                  return _t("character.create.success", name=character.name, main_status=character.main_status.name_hr)

            view = SpecSelectionView(click_callback, character_class, role)
            await ctx.respond(view=view, ephemeral=True)
          else:
            character = await add_character(sess, user_id, guild_id, name, role, character_class, main_status=main_status)
            await ctx.respond(_t("character.create.success", name=character.name, main_status=character.main_status.name_hr), ephemeral=True)
  
    except InvalidArgument as e:
      await ctx.respond(_t("character.create.error", error=str(e)), ephemeral=True)

  @character_group.command(description="Update a character")
  @guild_only()
  async def update(self, ctx, 
    name: str, 
    new_name: str = None, 
    main_status: Option(MainStatusEnum, description="Whether the character is a main or reroll.") = None, 
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None, 
    role: Option(RoleEnum, description="If specified, will also trigger spec update when relevant") = None, 
    character_class: Option(ClassEnum, name="class", description="If specified, will also trigger spec update when relevant") = None
  ):
    """Update a character (by name)
    """
    try:
      if main_status is None and new_name is None and role is None and character_class is None:
        raise InvalidArgument(_t("character.update.nothingtochange"))

      name = validate_character_name(name)
      new_name = validate_character_name(new_name)
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          old_character = await get_character(sess, guild_id, user_id, name)
          final_class = default_if_none(character_class, old_character.character_class)
          final_role = default_if_none(role, old_character.role)
          if (character_class is not None or role is not None) and SpecEnum.has_spec(final_class, final_role):

            # callback for spec button click
            async def click_callback(spec: SpecEnum):
              async with self.bot.db_session_class() as sess:
                async with sess.begin():
                  character = await update_character(sess, user_id, guild_id, name, new_name, main_status=main_status, role=final_role, spec=spec, character_class=final_class)
                  return _t("character.update.success", name=character.name, main_status=character.main_status.name_hr)

            view = SpecSelectionView(click_callback, final_class, final_role)
            await ctx.respond(view=view, ephemeral=True)
          
          else:
            character = await update_character(sess, user_id, guild_id, name, new_name, main_status=main_status, role=role, character_class=character_class)
            await ctx.respond(_t("character.update.success", name=character.name, main_status=character.main_status.name_hr), ephemeral=True)
    
    except InvalidArgument as e:
      await ctx.respond(_t("character.update.error", error=str(e)), ephemeral=True)

  @character_group.command(description="Delete a character")
  @guild_only()
  async def delete(self, ctx, name: str, for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None):
    """Delete a character
    """
    try:
      name = validate_character_name(name)
      guild_id = str(ctx.guild_id)
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          await delete_character(sess, user_id, guild_id, name)
          await ctx.respond(_t("character.delete.success"), ephemeral=True)
    
    except InvalidArgument as e:
      await ctx.respond(_t("character.delete.error", error=str(e)), ephemeral=True)


  @character_group.command(description="List of a user's characters")
  @guild_only()
  async def list(self, ctx, 
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
          query = select(Character).where(
            Character.id_user == user_id,
            Character.id_guild == guild_id
          ).order_by(Character.main_status.desc(), Character.name.asc())
          characters = (await sess.execute(query)).scalars().all()
          embed = CharacterListEmbed(characters)
          await ctx.respond(embed=embed, ephemeral=not public)

    except InvalidArgument as e:
      await ctx.respond(_t("character.list.error", str(e)), ephemeral=True)

  @character_group.command(description="")
  @commands.has_permissions(administrator=True)
  @guild_only()
  async def all(self, ctx,
    main_only: Option(bool, description="Main characters only.") = True,
    character_class: Option(ClassEnum, name="class", description="Only list characters with this class") = None,
    role: Option(RoleEnum, description="Only list characters with this role") = None,
    spec: Option(SpecEnum, description="Only list characters with this spec") = None,
    public: Option(bool, description="Whether or not to display the resulting list publicly.") = False
  ):
    guild_id = str(ctx.guild_id)
  
    async with self.bot.db_session_class() as sess:
      async with sess.begin():
        where_clause = [Character.id_guild == guild_id]
        if main_only:
          where_clause.append(Character.main_status == MainStatusEnum.MAIN)
        if character_class is not None:
          where_clause.append(Character.character_class == character_class)
        if role is not None:
          where_clause.append(Character.role == role)
        if spec is not None:
          where_clause.append(Character.spec == spec)
        
        query = select(Character).where(*where_clause).order_by(Character.id_user.asc(), Character.name.asc())
        characters = (await sess.execute(query)).scalars().all()
        embed = CharacterListEmbed(characters, display_user=True)
        await ctx.respond(embed=embed, ephemeral=not public)

  @commands.Cog.listener()
  async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
    logging.getLogger().error(str(error))
    raise error


def setup(bot):
  bot.add_cog(CharacterCog(bot))