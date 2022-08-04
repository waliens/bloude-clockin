


from xml.dom import InvalidAccessErr
from discord import Embed, InvalidArgument

from models import GuildCharter


class GuildCharterEmbed(Embed):
  def __init__(self, charter: GuildCharter, *args, section: int=None, sign_info: bool=False, **kwargs):
    super().__init__(*args, title=charter.title, **kwargs)

    fields = charter.fields
    if section is None and sign_info and charter.id_sign_message is not None:
      self.set_footer(f"React with <{charter.id_sign_emoji}> to accept the charter.")
    
    if section is not None:
      if  1 <= section <= len(charter.fields):
        fields = [f for f in charter.fields if f.number == section]
      else:
        raise InvalidArgument("invalid section number.")     
  
    for field in fields:
      self.add_field(name=f"({field.number}) " + field.title, value=field.content, inline=False)