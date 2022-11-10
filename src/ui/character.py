
import os
from discord.ui import Button

from ui.util import EMBED_DESCRIPTION_MAX_LENGTH
from db_util.wow_data import ClassEnum, MainStatusEnum, RoleEnum, SpecEnum
from discord import ButtonStyle, Interaction, InvalidArgument, Embed
from discord.ui import View

from pycord18n.extension import _ as _t


class SpecButton(Button):
  def __init__(self, callback, spec: SpecEnum, *args, **kwargs):
    """The parent view is tore down when a button is clicked
    Parameters
    ----------
    callback: async callable
      Async callable to handle the button click. It is passed the clicked spec. 
      Should return a success message to be sent to the user. 
      On error, should raise an invalid argument exception when it fails due to incorrect spec. 
      In this case, the exception message will be the one returned to the user.
    spec: SpecEnum
      The spec for this button
    """
    super().__init__(*args, label=spec.name_hr, **kwargs)
    self._callback = callback
    self._spec = spec

  async def callback(self, interaction: Interaction):
    try:
      self.view.disable_all_items()
      success_message = await self._callback(self._spec)
      await interaction.response.edit_message(content=success_message, view=None, embed=None)
    except InvalidArgument as e:
      await interaction.response.edit_message(content=str(e), view=None, embed=None)
    finally:
      self.view.stop()
      self.view.clear_items()
 

class SpecSelectionView(View):
  def __init__(self, click_callback, _class: ClassEnum, role: RoleEnum, *args, **kwargs):
    super().__init__(*args, **kwargs)

    for i, spec in enumerate(_class.get_specs(role)):
      self.add_item(SpecButton(click_callback, spec, style=ButtonStyle.primary, row=i))
    

class CharacterListEmbed(Embed):
  ETC_STR = "..."

  def __init__(self, characters, *args, display_user=False, **kwargs):
    super().__init__(*args, **kwargs)
    if len(characters) > 0:
      formatted = list()
      for c in sorted(characters, key=lambda c: (c.main_status.value, c.name)):
        descriptor = ":" + {RoleEnum.HEALER: "ambulance", RoleEnum.MELEE_DPS: "crossed_swords", RoleEnum.RANGED_DPS: "bow_and_arrow", RoleEnum.TANK: "shield"}[c.role] + ":"
        descriptor += " "
        if c.main_status == MainStatusEnum.MAIN:
          descriptor += "**"
        elif c.main_status == MainStatusEnum.REROLL:
          descriptor += "*"
        descriptor +=  c.name
        if c.main_status == MainStatusEnum.MAIN:
          descriptor += "**"
        elif c.main_status == MainStatusEnum.REROLL:
          descriptor += "*"
        descriptor +=  f" ({c.character_class.name_hr}"
        if c.spec is not None:
          descriptor += f" {c.spec.name_hr.lower()}"
        descriptor += ")"
        if display_user:
          descriptor += f" <@{c.id_user}>"
        if sum(map(len, formatted)) + len("\n") * len(formatted) + len(descriptor) < EMBED_DESCRIPTION_MAX_LENGTH - len("\n" + self.ETC_STR):
          formatted.append(descriptor)
        else:
          formatted.append(self.ETC_STR)
          break
      description = os.linesep.join(formatted)
    else:
      description = _t("character.list.noneregistered")

    self.description = description
    self.title = _t("character.list.title")