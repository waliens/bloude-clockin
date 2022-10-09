from collections import defaultdict

from discord import InvalidArgument
from sqlalchemy import or_, select, Integer, delete, func, not_
from db_util.character import get_character
from db_util.wow_data import InventorySlotEnum
from models import Character, Item, Loot, Recipe, UserRecipe

from sqlalchemy.exc import NoResultFound, IntegrityError, MultipleResultsFound

from pycord18n.extension import _ as _t


def strcmp_sql_fn(field, query, exact=True):
  if exact:
    return field.ilike(f"%{query}%")
  else:
    t_query = "%".join([c for c in query])
    return field.ilike(f"%{t_query}%")


async def items_search(sess, name: str=None, _id: int=None, max_items: int=-1, model_class=Item, filters=None):
  """At least name or id should be provided, otherwise invalid argument error is raised"""
  try:
    if _id is not None:
      id_query = select(model_class).where(model_class.id == _id)
      id_result = await sess.execute(id_query) 
      return [id_result.scalars().one()]

    if name is None:
      raise InvalidArgument(_t("item.invalid.missing.nameorid"))
 
    # attempt exact match 
    name_fields = [model_class.name_en, model_class.name_fr]
    exact_where_clause = [or_(*[strcmp_sql_fn(f, name) for f in name_fields])]
    if filters is not None and len(filters) > 0:
      exact_where_clause.extend(filters)
    exact_match_query = select(model_class).where(*exact_where_clause).order_by(model_class.id)
    if max_items > 0:
      exact_match_query = exact_match_query.limit(max_items)
    exact_results = await sess.execute(exact_match_query)
    exact_items = exact_results.scalars().all()

    if len(exact_items) > 0:
      return exact_items

    # no exact match 
    loose_where_clause = [or_(*[strcmp_sql_fn(f, name, exact=False) for f in name_fields])]
    if filters is not None and len(filters) > 0:
      loose_where_clause.extend(filters)
    loose_match_query = select(model_class).where(*loose_where_clause).order_by(model_class.id)
    if max_items > 0:
      loose_match_query = loose_match_query.limit(max_items)
    loose_results = await sess.execute(loose_match_query)
    loose_items = loose_results.scalars().all()
    
    if len(loose_items) > 0:
      return loose_items
    
    raise InvalidArgument(_t("item.invalid.nomatch"))
  except NoResultFound as e:
    raise InvalidArgument(_t("item.invalid.nomatch"))


async def register_loot(sess, item_id, character_id, in_dkp=False, commit=True):
  """Register a loot for the given character"""
  try:
    item = await sess.get(Item, item_id)
    maxcount = int(item.metadata_["maxcount"])

    cnt_query = select(func.count(Loot.id)).where(Loot.id_item == item_id, Loot.id_character == character_id)
    cnt_res = await sess.execute(cnt_query)
    loot_count = cnt_res.scalar()
   
    if maxcount == 0 or loot_count < maxcount:
      new_loot = Loot(id_item=item_id, id_character=character_id, in_dkp=in_dkp)
      sess.add(new_loot)
    else:
      raise InvalidArgument(_t("loot.invalid.toomany", count=maxcount))

    if commit:
      await sess.commit()
  except IntegrityError as e:
    raise InvalidArgument(_t("item.invalid.alreadyrecorded"))


async def register_bulk_loots(sess, guild_id, loots_maps: dict, in_dkp=False):
  """"""
  for character_name, item_ids in loots_maps.items():
    # extract character
    try:
      char_result = await sess.execute(select(Character).where(Character.name == character_name, Character.id_guild == guild_id))
      character = char_result.scalars().one()
    except NoResultFound:
      raise InvalidArgument(_t("loot.invalid.nocharacter", character_name=character_name))
    except MultipleResultsFound:
      raise InvalidArgument(_t("loot.invalid.multiplecharacters", character_name=character_name))

    for item_id in item_ids:
      try:
        await register_loot(sess, item_id, character.id, in_dkp=in_dkp, commit=False)
      except InvalidArgument:
        raise InvalidArgument(_t("item.invalid.alreadyrecorded_withinfo", item_id=item_id, character_name=character_name))

  await sess.commit()


async def register_user_recipes(sess, recipe_ids, character_id, do_commit=False):
  """Register a recipe for the given character"""
  try:
    # get already recorded recipes
    query = select(UserRecipe).where(UserRecipe.id_character == character_id, UserRecipe.id_recipe.in_(recipe_ids))
    result = await sess.execute(query)
    existing_recipes = result.scalars().all()
    existing_ids = set([r.id_recipe for r in existing_recipes])

    # create newly added ones
    new_recipes = [
      UserRecipe(id_recipe=recipe_id, id_character=character_id)
      for recipe_id in recipe_ids
      if recipe_id not in existing_ids
    ]
    sess.add_all(new_recipes)
    if do_commit:
      await sess.commit()
    return new_recipes
  except IntegrityError:
    raise InvalidArgument(_t("recipe.invalid.alreadyrecorded"))


async def fetch_loots(sess, character_id: int, slot: InventorySlotEnum=None, max_items: int=-1):
  """Fetch loots"""
  where_clause = [Loot.id_character == character_id]
  query = select(Loot).order_by(Loot.created_at.desc())
  
  # add slot filter
  if slot is not None:
    inventory_types = [e.value for e in slot.get_inventory_types()]
    if len(inventory_types) > 0:
      where_clause.append(Loot.item.has(Item.metadata_['InventoryType'].astext.cast(Integer).in_(inventory_types)))
  
  # limit number of results
  if max_items > 0:
    query = query.limit(max_items)
  
  query = query.where(*where_clause)
  
  result = await sess.execute(query)
  return result.scalars().all()


async def remove_loots(sess, character_id: int, item_id: int, only_last=True, force_remove_in_dkp=False):
  where_clause = [
    Loot.id_character == character_id, 
    Loot.id_item == item_id
  ]
  if not force_remove_in_dkp:
    where_clause.append(not_(Loot.in_dkp))
  if only_last:
    where_clause = [Loot.id.in_(select(Loot.id).where(*where_clause).order_by(Loot.created_at.desc()).limit(1))]

  query = select(Loot).where(*where_clause)
  results = await sess.execute(query)
  loots = results.scalars().all()

  for loot in loots:
    await sess.delete(loot)
  

async def get_crafters(sess, recipe_ids):
  # get recipes
  recipes = await get_recipes(sess, recipe_ids)

  # get user recipes
  query = select(UserRecipe).where(UserRecipe.id_recipe.in_(recipe_ids))
  result = await sess.execute(query)
  user_recipes = result.scalars().all()

  # structure as a list of tuples
  recipe_characters = defaultdict(list)
  for user_recipe in user_recipes:
    recipe_characters[user_recipe.id_recipe].append(user_recipe.character)
  
  return [(recipe, recipe_characters[recipe.id]) for recipe in recipes]


async def get_recipes(sess, recipe_ids):
  recipes_query = select(Recipe).where(Recipe.id.in_(recipe_ids))
  recipes_result = await sess.execute(recipes_query)
  return recipes_result.scalars().all()


async def get_character_recipes(sess, id_guild, character_name, user_id, profession=None):
  # extract the character
  character = await get_character(sess, id_guild, id_user=user_id, name=character_name)

  # query recipes
  where_clause = [UserRecipe.character.has(id=character.id)]
  if profession is not None:
    where_clause.append(UserRecipe.recipe.has(profession=profession))
  query = select(UserRecipe).where(*where_clause)
  results = await sess.execute(query)
  return results.scalars().all()


async def remove_user_recipes(sess, character_id, recipe_ids):
  query = delete(UserRecipe).where(UserRecipe.id_character == character_id, UserRecipe.id_recipe.in_(recipe_ids))
  await sess.execute(query)
  