import discord
from discord.ext import commands   
from discord import InvalidArgument, Option, guild_only

from cogs.util import get_applied_user_id

from pycord18n.extension import _ as _t

from db_util.character import get_character
from db_util.item import get_character_recipes, get_crafters, get_recipes, items_search, register_user_recipes, remove_user_recipes
from db_util.wow_data import ProfessionEnum
from models import Recipe
from ui.item import RecipeCraftersEmbed, RecipeCraftersListSelectorView, RecipeListEmbed, RecipeRegistrationListSelectorView, UserRecipeEmbed


class RecipeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  recipe_group = discord.SlashCommandGroup("recipe", description="Commands for managing recipes.")

  @recipe_group.command(description="Add one or more recipes to a character.")
  @guild_only()
  async def add(self, ctx, 
    profession: Option(ProfessionEnum, description="Search for a recipe for this profession (ignored if `recipe_ids` is provided).") = None,
    recipe_name: Option(str, description="A name to look for the recipe (ignored if `recipe_ids` is provided).") = None,
    recipe_ids: Option(str, name="ids", description="A comma-separated list of recipe spell identifiers.") = None,
    char_name: Option(str, name="character", description="The character who has the recipe. By default, the main character of the user.") = None,
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None
  ):
    try:
      if (recipe_name is None or profession is None) and recipe_ids is None:
        raise InvalidArgument(_t("recipe.invalid.missinginfo"))
      
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          await ctx.defer(ephemeral=True)
          character = await get_character(sess, guild_id, user_id, char_name)
          if recipe_ids is not None:
            user_recipes = await register_user_recipes(sess, [int(v.strip()) for v in recipe_ids.split(",")], character.id)
            recipes = await get_recipes(sess, [ur.id_recipe for ur in user_recipes])
            embed = RecipeListEmbed(recipes, title=_t("recipe.add.embed.title"), max_items=25, show_ids=True)
            await ctx.respond(embed=embed, ephemeral=True)
          else:
            max_recipes = 10
            recipes = await items_search(sess, recipe_name, _id=None, max_items=max_recipes + 1, model_class=Recipe, filters=[Recipe.profession == profession])
            recipe_list_embed = RecipeListEmbed(recipes, max_items=max_recipes, title=_t("general.ui.list.matching"))
            reciper_list_selector_view = RecipeRegistrationListSelectorView(self.bot, recipes, character.id, max_recipes=max_recipes)
            await ctx.respond(embed=recipe_list_embed, view=reciper_list_selector_view, ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.add.error", error=str(e)), ephemeral=True)

  @recipe_group.command(description="List the recipes of a character.")
  @guild_only()
  async def list(self, ctx,
    profession: Option(ProfessionEnum, description="Filter by profession (optional).") = None,
    char_name: Option(str, name="character", description="The character whose recipes should be listed. By default, the main character of the user.") = None,
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None,
    show_ids: Option(bool, description="True to display recipes identifiers, defaults to False.") = False,
    show_dates: Option(bool, description="True to display recipes acquisition dates, defaults to False.") = False,
    public: Option(bool, description="True to display the list publicly, defaults to False.") = False
  ):
    try:
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id), requires_admin=False)
      guild_id = str(ctx.guild_id)
      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          await ctx.defer(ephemeral=not public)
          character = await get_character(sess, guild_id, user_id, char_name)
          user_recipes = await get_character_recipes(sess, guild_id, character_name=char_name, user_id=user_id, profession=profession)
          embed = UserRecipeEmbed(character, user_recipes, one_profession=profession, show_ids=show_ids, show_dates=show_dates)
          await ctx.respond(embed=embed, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.list.error", error=str(e)), ephemeral=True)

  @recipe_group.command(description="Find a crafter for one or several recipes.")
  @guild_only()
  async def crafters(self, ctx,
    profession: Option(ProfessionEnum, description="Search for a recipe for this profession (ignored if `recipe_ids` is provided).") = None,
    recipe_name: Option(str, description="A name to look for the recipe (ignored if `recipe_ids` is provided).") = None,
    recipe_ids: Option(str, name="ids", description="A comma-separated list of recipe spell identifiers.") = None,
    public: Option(bool, description="To show the response publicly") = False,
    show_ids: Option(bool, description="To display recipe identifiers in the response message.") = False
  ):
    try:
      await ctx.defer(ephemeral=not public)
      if recipe_ids is None and (recipe_name is None or profession is None):
        raise InvalidArgument(_t("recipe.invalid.missinginfo"))

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          if recipe_ids is not None:
            crafters = await get_crafters(sess, [int(v.strip()) for v in recipe_ids.split(",")])
            embed = RecipeCraftersEmbed(crafters, show_ids=show_ids)
            await ctx.respond(embed=embed, ephemeral=not public)
          else:
            max_recipes = 10
            recipes = await items_search(sess, recipe_name, _id=None, max_items=max_recipes + 1, model_class=Recipe, filters=[Recipe.profession == profession])
            recipe_list_embed = RecipeListEmbed(recipes, max_items=max_recipes, title=_t("general.ui.list.matching"))
            reciper_list_selector_view = RecipeCraftersListSelectorView(self.bot, recipes, show_ids=show_ids, max_recipes=max_recipes)
            await ctx.respond(embed=recipe_list_embed, view=reciper_list_selector_view, ephemeral=not public)
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.crafters.error", error=str(e)), ephemeral=not public)

  @recipe_group.command(description="")
  @guild_only()
  async def remove(self, ctx, 
    recipe_ids: Option(str, name="ids", description="A comma-separated list of recipe spell identifiers."),
    char_name: Option(str, name="character", description="The character whose recipes should be removed. By default, the main character of the user.") = None,
    for_user: Option(discord.Member, description="The user the character belongs to. By default, the user is you.") = None
  ):
    try:
      await ctx.defer(ephemeral=True)
      if recipe_ids is None:
        raise InvalidArgument(_t("recipe.invalid.missing.ids"))
      
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          character = await get_character(sess, guild_id, id_user=user_id, name=char_name)
          await remove_user_recipes(sess, character.id, [int(v.strip()) for v in recipe_ids.split(",")])
          await ctx.respond(_t("recipe.remove.success"), ephemeral=True)
  
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.remove.error", error=str(e)), ephemeral=True)


def setup(bot):
  bot.add_cog(RecipeCog(bot))