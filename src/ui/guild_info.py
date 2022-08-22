
from discord import Embed, InvalidArgument
from pycord18n.extension import _ as _t

from models import GuildCharter



class GuildCharterEmbed(Embed):
  def __init__(self, charter: GuildCharter, *args, section: int=None, sign_info: bool=False, **kwargs):
    super().__init__(*args, title=charter.title, **kwargs)

    fields = sorted(charter.fields, key=lambda f: f.number)
    if section is None and sign_info and charter.sign_emoji is not None:
      self.set_footer(text=_t("charter.show.ui.react", emoji=charter.sign_emoji))
    
    if section is not None:
      if  1 <= section <= len(charter.fields):
        fields = [f for f in charter.fields if f.number == section]
      else:
        raise InvalidArgument(_t("charter.section.invalid.number"))     
  
    for field in fields:
      self.add_field(name=f"({field.number}) " + field.title, value=field.content, inline=False)
