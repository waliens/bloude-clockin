
from pygsheets import Spreadsheet, Worksheet
from item_priorities.priorities import PriorityList


class ItemWithPriority(object):
  def __init__(self, item_id: int, priority_list: PriorityList, **metadata):
    self._item_id = item_id
    self._priority_list = priority_list
    self._metadata = metadata


class PrioParser(object):
  PRIO_SHEET_TITLE_PREFIX = "prio_"
  CONFIG_SHEET_NAME = "config_roles"

  def __init__(self, gsheet: Spreadsheet) -> None:
    self._gsheet = gsheet
    self._name2role = self._parse_roles()
    self._role2name = {v: k for k, v in self._name2role.items()}
    self._item_prio = dict()
    for ws in gsheet.worksheets():
      if not ws.title.startswith(self.PRIO_SHEET_TITLE_PREFIX):
        continue
      new_items = self._read_prio_sheet(ws)
      interesected_items = set(new_items.keys()).intersection(self._item_prio.keys())
      if len(interesected_items) > 0:
        raise ParseError("duplicate items in different sheets")
      for k, v in new_items.items():
        self._item_prio[k] = v

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

    items = dict()
    for row in values[1:]:
      if len(row[columns["id"]].strip()) == 0:
        continue
      item_id = int(row[columns["id"]])
      
      priorities = list()
      for curr_item in row[6:]:
        value = None
        if curr_item in self._name2role:
          value = self._name2role[curr_item]
        elif curr_item in PrioTierEnum.__members__:
          value = curr_item
        priorities.append(value)

      items[item_id] = ItemWithPriority(
        item_id=item_id,
        priority_list=PriorityList(priorities),
        boss=row[columns["boss"]]
      )
    
    return items

  @property
  def name2role(self):
    return self._name2role
