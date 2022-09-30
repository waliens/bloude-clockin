
from discord import Embed
from pycord18n.extension import _ as _t


class SheetParserErrorsEmbed(Embed):
  MAX_DESC_LENGTH = 4096

  def __init__(self, errors, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._errors = errors
    self.title = _t("gsheet.errors.ui.title")

    desc = ""
    for error in errors:
      error_txt = str(error)
      if len(desc) + len(error_txt) + 3 >= self.MAX_DESC_LENGTH:
        break
      desc += f"- {error_txt}\n"
    
    self.description = desc