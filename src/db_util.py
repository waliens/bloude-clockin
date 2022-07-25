import datetime
from sqlalchemy import select, update
from models import Character


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
  created: bool
    True if a new character has been created, False otherwise
  character: models.Character
    The character object, a new one if created is True, the existing character with 
    the same name if created is False
  """
  where_clause = [Character.id_guild == id_guild, Character.id_user == id_user]
  query = select(Character).where(*where_clause)
  user_characters = (await session.execute(query)).mappings().all()
  if len(user_characters) == 0 or len([c for c in user_characters if c['Character'].name == name]) == 0:
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
    return True, new_character
  else:
    return False, None