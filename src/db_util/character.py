import datetime
from discord import InvalidArgument
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum, is_valid_class_role
from models import Character


def has_character_by_name(models, name):
  return len([c for c in models if c.name.lower() == name.lower()]) > 0


def get_character_by_name(models, name):
  return [c for c in models if c.name.lower() == name.lower()][0]


async def add_character(session, id_user: str, id_guild: str, name: str, role: RoleEnum, character_class: ClassEnum, spec: SpecEnum=None, is_main: bool=False):
  """Adds a character, if not exists
  Parameters
  ----------
  session: 
    Database session
  id_user: snowflake (str)
    Discord user identifier
  id_guild: snowflake (str)
    Discord guild identifier
  name: str
    Character name
  role: RoleEnum
    The role of the character

  character_class: ClassEnum
    The class of the character
  spec: SpecEnum (optional)
    The character's spec, None for no specific spec
  is_main: bool (optional)
    Whether or not the character should be the main one


  Returns
  -------
  character: models.Character
    The created character object
  """
  where_clause = [Character.id_guild == id_guild, Character.id_user == id_user]
  query = select(Character).where(*where_clause)
  user_characters = (await session.execute(query)).scalars().all()

  if not is_valid_class_role(character_class, role):
    raise InvalidArgument(f'invalid class/role combination')

  if spec is not None and not spec.is_valid_for_class_role(character_class, role):
    raise InvalidArgument(f"invalid spec for class/role combination")
  
  if len(user_characters) > 0 and has_character_by_name(user_characters, name):
    raise InvalidArgument(f"such a character '{name}' already exists.")

  new_character = Character(
    name=name, 
    id_guild=id_guild, 
    id_user=id_user, 
    is_main=len(user_characters) == 0 or is_main, 
    created_at=datetime.datetime.now(),
    role=role,
    spec=spec,
    character_class=character_class
  )

  if is_main:
    await session.execute(update(Character).where(*where_clause).values(is_main=False))
  session.add(new_character)
  await session.commit()
  return new_character
  

async def update_character(session, id_user: str, id_guild: str, name: str, new_name: str = None, is_main: bool = False, role: RoleEnum=None, character_class: ClassEnum=None, spec: SpecEnum=None):
  """Updates a character
  Parameters
  ----------
  session: 
    Database session
  id_user: snowflake (str)
    Discord user identifier
  id_guild: snowflake (str)
    Discord guild identifier
  name: str 
    Name of the character to update
  new_name: str (optional)
    New name for the character
  is_main: bool (optional)
    New main status
  role: RoleEnum (optional)
    The role of the character
  character_class: ClassEnum (optional)
    The class of the character
  spec: SpecEnum (optional)
    The spec of the character

  Returns
  -------
  character: models.Character
    The updated character object
  """
  where_clause = [Character.id_guild == id_guild, Character.id_user == id_user]
  query = select(Character).where(*where_clause)
  user_characters = (await session.execute(query)).scalars().all()
  
  if len(user_characters) == 0 or not has_character_by_name(user_characters, name):
    raise InvalidArgument(f"unknown character '{name}'.")

  current_character = get_character_by_name(user_characters, name)

  if not current_character.is_main and is_main:
    await session.execute(update(Character).where(*where_clause).values(is_main=False))

  if new_name is not None:
    if has_character_by_name(user_characters, new_name):
      raise InvalidArgument(f"such a character '{new_name}' already exists.")
    current_character.name = new_name
  
  if is_main is not None:
    if not is_main:
      raise InvalidArgument("to change your main character, select the new main rather than unselect the old one.")
    current_character.is_main = new_name = True

  if role is not None:
    current_character.role = role

  if character_class is not None:
    current_character.character_class = character_class

  if not is_valid_class_role(current_character.character_class, current_character.role):
    raise InvalidArgument(f'invalid class/role combination')
  
  current_spec = current_character.spec
  possible_specs = set(current_character.character_class.get_specs(current_character.role))
  invalid_spec_message = "invalid spec for this class/role combination"
  if SpecEnum.has_spec(current_character.character_class, current_character.role):
    if spec is not None and spec in possible_specs:
      current_character.spec = spec
    elif not (spec is None and current_spec in possible_specs):
      raise InvalidArgument(invalid_spec_message) 
  else:
    if spec is None:
      current_character.spec = None
    else:
      raise InvalidArgument(invalid_spec_message)

  await session.commit()

  return current_character


async def delete_character(session, id_user: str, id_guild: str, name: str):
  """Deletes a character, if not main
  Parameters
  ----------
  session: 
    Database session
  id_user: snowflake (str)
    Discord user identifier
  id_guild: snowflake (str)
    Discord guild identifier
  name: str
    Character name (to delete)
  """
  try:
    where_clause = [Character.id_guild == id_guild, Character.id_user == id_user, func.lower(Character.name) == name.lower()]
    character = (await session.execute(select(Character).where(*where_clause))).scalars().one_or_none()
    if character is None:
      return
    elif character.is_main:
      raise InvalidArgument("cannot delete the main character")
    await session.delete(character)
    await session.commit()
  except MultipleResultsFound:
    raise InvalidArgument("multiple characters found")


async def get_character(session, id_guild, id_user, name=None):
  """Return the character based on the filter parameters. If name is omitted (None), 
  the main character for this user and guild is returned.
  """
  try:
    where_clause = [Character.id_guild == id_guild, Character.id_user == id_user]
    if name is not None:
      where_clause.append(Character.name.ilike(f"%{name}%"))
    else:
      where_clause.append(Character.is_main)
    results = await session.execute(select(Character).where(*where_clause))
    return results.scalars().one()
  except NoResultFound as e:
    raise InvalidArgument("character not found")
