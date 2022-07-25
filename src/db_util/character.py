import datetime
from discord import InvalidArgument
from sqlalchemy import delete, select, update
from models import Character


def has_character_by_name(models, name):
  return len([c for c in models if c.name == name]) > 0


def get_character_by_name(models, name):
  return [c for c in models if c.name == name][0]


async def add_character(session, id_user: str, id_guild: str, name: str, is_main: bool=False):
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
  is_main: bool
    Whether or not the character should be the main one

  Returns
  -------
  character: models.Character
    The created character object
  """
  where_clause = [Character.id_guild == id_guild, Character.id_user == id_user]
  query = select(Character).where(*where_clause)
  user_characters = (await session.execute(query)).scalars().all()
  
  if len(user_characters) > 0 and has_character_by_name(user_characters, name):
    raise InvalidArgument(f"such a character '{name}' already exists.")

  new_character = Character(
    name=name, 
    id_guild=id_guild, 
    id_user=id_user, 
    is_main=len(user_characters) == 0 or is_main, 
    created_at=datetime.datetime.now()
  )

  if is_main:
    await session.execute(update(Character).where(*where_clause).values(is_main=False))
  session.add(new_character)
  await session.commit()
  return new_character
  

async def update_character(session, id_user: str, id_guild: str, name: str, new_name: str = None, is_main: bool = False):
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
  
  update_data = {}

  if new_name is not None:
    if has_character_by_name(user_characters, new_name):
      raise InvalidArgument(f"such a character '{new_name}' already exists.")
    update_data['name'] = new_name
  
  if is_main is not None:
    if not is_main:
      raise InvalidArgument("to change your main character, select the new main rather than unselect the old one.")
    update_data['is_main'] = True

  current_character = get_character_by_name(user_characters, name)

  if not current_character.is_main and is_main:
    await session.execute(update(Character).where(*where_clause).values(is_main=False))
  await session.execute(update(Character).where(*where_clause, Character.name == name).values(**update_data))

  await session.commit()

  return await session.get(Character, current_character.id)


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
  where_clause = [Character.id_guild == id_guild, Character.id_user == id_user, Character.name == name]
  character = (await session.execute(select(Character).where(*where_clause))).scalars().first()
  if character is not None and character.is_main:
    raise InvalidArgument("cannot delete the main character")
  await session.execute(delete(Character).where(*where_clause))
  await session.commit()