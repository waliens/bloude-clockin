import discord
from discord.ext import commands   
from discord import InvalidArgument, Option, guild_only

from cogs.util import get_applied_user_id

from pycord18n.extension import _ as _t

from db_util.character import get_character
from db_util.item import get_crafters, items_search
from db_util.wow_data import ProfessionEnum
from models import Recipe
from ui.item import RecipeCraftersEmbed, RecipeCraftersListSelectorView, RecipeListEmbed, RecipeRegistrationListSelectorView


class RecipeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  recipe_group = discord.SlashCommandGroup("recipe", description="Commands for managing recipes.")

  @recipe_group.command(description="Register a recipe.")
  @guild_only()
  async def register(self, ctx, 
    profession: Option(ProfessionEnum, description="Search for a recipe for this profession (ignored if `recipe_ids` is provided)."),
    recipe_name: Option(str, description="A name to look for the recipe (ignored if `recipe_ids` is provided).") = None,
    recipe_id: Option(int, name="id", description="The recipe identifier.") = None,
    char_name: Option(str, name="character", description="The character who has the recipe. By default, the main character of the user.") = None,
    for_user: discord.Member = None
  ):
    try:
      await ctx.defer()
      if recipe_name is None and (profession is None or recipe_id is None):
        raise InvalidArgument(_t("recipe.invalid.missinginfo"))
      
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          max_recipes = 10
          character = await get_character(sess, guild_id, user_id, char_name)
          recipes = await items_search(sess, recipe_name, recipe_id, max_items=max_recipes + 1, model_class=Recipe, filters=[Recipe.profession == profession])
          recipe_list_embed = RecipeListEmbed(recipes, max_items=max_recipes, title=_t("general.ui.list.matching"))
          reciper_list_selector_view = RecipeRegistrationListSelectorView(self.bot, recipes, character.id, max_recipes=max_recipes)
          await ctx.respond(embed=recipe_list_embed, view=reciper_list_selector_view, ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.add.error", error=str(e)), ephemeral=True)


  @recipe_group.command(description="Find a crafter for one or several recipes.")
  @guild_only()
  async def crafters(self, ctx,
    profession: Option(ProfessionEnum, description="Search for a recipe for this profession (ignored if `recipe_ids` is provided).") = None,
    recipe_name: Option(str, description="A name to look for the recipe (ignored if `recipe_ids` is provided).") = None,
    recipe_ids: Option(str, description="A comma-separated list of recipe identifiers.") = None,
    public: Option(bool, description="To show the response publicly") = False,
    show_ids: Option(bool, description="To display recipe identifiers in the response message.") = False
  ):
    try:
      await ctx.defer()
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


def setup(bot):
  bot.add_cog(RecipeCog(bot))