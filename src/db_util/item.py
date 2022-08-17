import datetime

from discord import InvalidArgument
import pytz
from sqlalchemy import or_, select
from models import Item, Loot

from sqlalchemy.exc import NoResultFound, IntegrityError


def strcmp_sql_fn(field, query, exact=True):
  if exact:
    return field.ilike(f"%{query}%")
  else:
    t_query = "%".join([c for c in query])
    return field.ilike(f"%{t_query}%")


async def items_search(sess, name=None, _id=None, max_items=-1):
  """At least name or id should be provided, otherwise invalid argument error is raised"""
  try:
    if _id is not None:
      id_query = select(Item).where(Item.id == _id)
      id_result = await sess.execute(id_query) 
      return id_result.scalars().one()

    if name is None:
      raise InvalidArgument("missing name or id information.")
 
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
    
    raise InvalidArgument("no matching item found.")

  except NoResultFound as e:
    raise InvalidArgument("no matching item found.")


async def register_loot(sess, item_id, character_id):
  """Register a loot for the given character"""
  try:
    new_loot = Loot(
      id_item=item_id, 
      id_character=character_id, 
      created_at=datetime.datetime.now(tz=pytz.UTC).replace(tzinfo=None))
    sess.add(new_loot)
    await sess.commit()
  except IntegrityError as e:
    raise InvalidArgument("this loot was already recorded.")