import datetime

from discord import InvalidArgument
import pytz
from sqlalchemy import or_, select, Integer
from db_util.wow_data import InventorySlotEnum
from models import Item, Loot

from sqlalchemy.exc import NoResultFound, IntegrityError

from pycord18n.extension import _ as _t


def strcmp_sql_fn(field, query, exact=True):
  if exact:
    return field.ilike(f"%{query}%")
  else:
    t_query = "%".join([c for c in query])
    return field.ilike(f"%{t_query}%")


async def items_search(sess, name: str=None, _id: int=None, max_items: int=-1):
  """At least name or id should be provided, otherwise invalid argument error is raised"""
  try:
    if _id is not None:
      id_query = select(Item).where(Item.id == _id)
      id_result = await sess.execute(id_query) 
      return [id_result.scalars().one()]

    if name is None:
      raise InvalidArgument(_t("item.invalid.missing.nameorid"))
 
    # attempt exact match 
    name_fields = [Item.name_en, Item.name_fr]
    exact_match_query = select(Item).where(or_(*[strcmp_sql_fn(f, name) for f in name_fields])).order_by(Item.id)
    if max_items > 0:
      exact_match_query = exact_match_query.limit(max_items)
    exact_results = await sess.execute(exact_match_query)
    exact_items = exact_results.scalars().all()

    if len(exact_items) > 0:
      return exact_items

    # no exact match 
    loose_match_query = select(Item).where(or_(*[strcmp_sql_fn(f, name, exact=False) for f in name_fields])).order_by(Item.id)
    if max_items > 0:
      loose_match_query = loose_match_query.limit(max_items)
    loose_results = await sess.execute(loose_match_query)
    loose_items = loose_results.scalars().all()
    
    if len(loose_items) > 0:
      return loose_items
    
    raise InvalidArgument(_t("item.invalid.nomatch"))
  except NoResultFound as e:
    raise InvalidArgument(_t("item.invalid.nomatch"))


async def register_loot(sess, item_id, character_id):
  """Register a loot for the given character"""
  try:
    loot = await sess.get(Loot, {"id_item": item_id, "id_character": character_id})
    if loot is None:
      new_loot = Loot(id_item=item_id, id_character=character_id, count=1)
      sess.add(new_loot)
    else:
      maxcount = int(loot.item.metadata_["maxcount"])
      if maxcount == 0 or loot.count < maxcount:
        loot.count += 1
      else:
        raise InvalidArgument(_t("loot.invalid.toomany", count=maxcount))
    await sess.commit()
  except IntegrityError as e:
    raise InvalidArgument(_t("item.invalid.alreadyrecorded"))


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
