
from discord.ui import Button

from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum
from discord import ButtonStyle, Interaction, InvalidArgument
from discord.ui import View


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
    


