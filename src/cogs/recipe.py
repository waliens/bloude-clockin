import discord
from discord.ext import commands   
from discord import InvalidArgument, Option, guild_only

from cogs.util import get_applied_user_id

from pycord18n.extension import _ as _t

from db_util.character import get_character
from db_util.item import items_search
from db_util.wow_data import ProfessionEnum
from models import Recipe
from ui.item import RecipeListEmbed, RecipeListSelectorView


class RecipeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  recipe_group = discord.SlashCommandGroup("recipe", description="Commands for managing recipes.")

  @recipe_group.command(description="Register a recipe.")
  @guild_only()
  async def register(self, ctx, 
    profession: Option(ProfessionEnum, description="The profession to register the recipe for."),
    item_name: Option(str, description="A query for the recipe name (if item_id is not provided).")= None,
    item_id: Option(int, name="id", description="The item id (if item_name is not provided).") = None,
    char_name: Option(str, name="character", description="The character who has the recipe. By default, the main character of the user.") = None,
    for_user: discord.Member = None
  ):
    try:
      if item_name is None and item_id is None:
        raise InvalidArgument(_t("recipe.invalid.missinginfo"))
      if item_name is not None and item_id is not None:
        raise InvalidArgument(_t("recipe.invalid.toomuchinfo"))
      
      user_id = get_applied_user_id(ctx, for_user, str(ctx.author.id))
      guild_id = str(ctx.guild_id)

      async with self.bot.db_session_class() as sess:
        async with sess.begin():
          max_recipes = 10
          character = await get_character(sess, guild_id, user_id, char_name)
          recipes = await items_search(sess, item_name, item_id, max_items=max_recipes + 1, model_class=Recipe, filters=[Recipe.profession == profession])
          recipe_list_embed = RecipeListEmbed(recipes, max_items=max_recipes, title=_t("general.ui.list.matching"))
          reciper_list_selector_view = RecipeListSelectorView(self.bot, recipes, character.id, max_recipes=max_recipes)
          await ctx.respond(embed=recipe_list_embed, view=reciper_list_selector_view, ephemeral=True)
    except InvalidArgument as e:
      await ctx.respond(_t("recipe.add.error", error=str(e)), ephemeral=True)