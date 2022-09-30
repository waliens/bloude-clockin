
from pygsheets import Spreadsheet, Worksheet, Cell
from db_util.wow_data import ClassEnum, RoleEnum, SpecEnum
from db_util.priorities import ItemWithPriority, ParseError, PriorityError, PriorityList, SepEnum, enum_get


class PrioParser(object):
  PRIO_SHEET_TITLE_PREFIX = "prio_"
  CONFIG_SHEET_NAME = "config_roles"

  def __init__(self, gsheet: Spreadsheet) -> None:
    self._gsheet = gsheet
    self._name2role = self._parse_roles()
    self._role2name = {v: k for k, v in self._name2role.items()}
    self._item_prio = dict()
    self._errors = list()
    for ws in gsheet.worksheets():
      if not ws.title.startswith(self.PRIO_SHEET_TITLE_PREFIX):
        continue
      new_items, ws_errors = self._read_prio_sheet(ws)
      interesected_items = set(new_items.keys()).intersection(self._item_prio.keys())
      if len(interesected_items) > 0:
        raise ParseError("duplicate items in different sheets")
      for k, v in new_items.items():
        self._item_prio[k] = v
      self._errors.extend(ws_errors.values())

  @property
  def items(self):
    return self._item_prio

  @property
  def errors(self):
    return self._errors

  def __getitem__(self, index):
    return self._item_prio[int(index)]

  def __len__(self):
    return len(self._item_prio)

  def _parse_roles(self):
    ws = self._gsheet.worksheet_by_title(self.CONFIG_SHEET_NAME)
    EXPECTED_HEADERS = ["class", "role", "spec", "name"]
    values = ws.get_all_values()
    headers = values[0]
    columns = {header: headers.index(header) for header in EXPECTED_HEADERS}

    # iterate
    name_map = dict()
    for row in values[1:]:      
      cls = enum_get(ClassEnum, row[columns["class"]], None)
      role = enum_get(RoleEnum, row[columns["role"]], None)
      spec = enum_get(SpecEnum, row[columns["spec"]], None)
      if cls is None or role is None:
        continue
      name_map[row[columns["name"]]] = (cls, role, spec)
    
    return name_map

  def _read_prio_sheet(self, ws: Worksheet):
    PRIO_COLUMNS = ['id', 'boss', 'comment']
    values = ws.get_all_values()
    headers = values[0]
    columns = {header: headers.index(header) for header in PRIO_COLUMNS}
    errors = dict()
    items = dict()
    row_offset, col_offset = 1, 6
    for row_index, row in enumerate(values[row_offset:]):
      try:
        if len(row[columns["id"]].strip()) == 0:
          continue
        item_id = int(row[columns["id"]])
        
        priorities = list()
        for col_index, curr_item in enumerate(row[col_offset:]):
          value = None
          if curr_item in self._name2role:
            value = self._name2role[curr_item]
          elif SepEnum.is_valid(curr_item):
            value = curr_item
          elif len(curr_item.strip()) > 0:
            raise ParseError(
              row_index + row_offset, 
              col_index + col_offset,
              f"unknown symbol '{curr_item}'"
            )
          priorities.append(value)

        items[item_id] = ItemWithPriority(
          item_id=item_id,
          priority_list=PriorityList(priorities),
          boss=row[columns["boss"]]
        )
      except ParseError as e:
        errors[e.row] = e
      except PriorityError as e:
        abs_row = row_index + row_offset
        errors[abs_row] = ParseError(abs_row, col_offset + e.col_index, parent=e)

    return items, errors

  @property
  def name2role(self):
    return self._name2role
