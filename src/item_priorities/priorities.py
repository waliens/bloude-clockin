from collections import defaultdict
from enum import Enum


class ParseError(Exception):
  pass


class PriorityError(ParseError):
  pass


class InvalidSepError(PriorityError):
  def __init__(self, sep, *args: object) -> None:
    super().__init__(f"expected separator, got '{sep}'", *args)
    self._sep = sep


class DuplicateRoleError(PriorityError):
  def __init__(self, duplicate, *args) -> None:
    super().__init__(f"duplicate role {duplicate}", *args)
    self._duplicate = duplicate

  @property
  def duplicate(self):
    return self._duplicate


class PrioTierEnum(Enum):
  IS_BIS = 5
  IS_ALMOST_BIS = 15
  IS_AVERAGE = 25
  IS_A_UP = 35
  IS_USELESS = 100 


def enum_get(e: Enum, k, default=None):
  try:
    return e[k]
  except KeyError:
    return default


class PriorityList(object):
  SEP_TIER = ">>"
  SEP_BETTER = ">"
  SEP_EQUAL = "~"

  def __init__(self, prio_array: list) -> None:
    self._priorities = self._parse(prio_array)

  @property
  def priorities(self):
    return [PrioTierEnum.IS_BIS, PrioTierEnum.IS_ALMOST_BIS, PrioTierEnum.IS_AVERAGE, PrioTierEnum.IS_A_UP, PrioTierEnum.IS_USELESS]

  def _parse(self, array):
    prios = defaultdict(list)
    already_processed = set()
    curr_index = 0
    for curr_tier in self.priorities[:-1]:
      prios[curr_tier].append(set())
      while curr_index < len(array):
        elem = array[curr_index]
        curr_index += 1
        if elem is None:
          continue
        if isinstance(elem, str):  # sep:
          if elem == self.SEP_TIER or elem is None or len(elem.strip()) == 0:
            break
          elif elem == self.SEP_EQUAL:
            continue
          elif elem == self.SEP_BETTER:
            prios[curr_tier].append(set())
          else: raise InvalidSepError(elem)
        else:
          if elem in already_processed:
            raise DuplicateRoleError(elem)
          already_processed.add(elem)
          prios[curr_tier][-1].add(elem)
    return prios

  def get_priority_tier(self, query):
    for tier_prio, sublevels in self._priorities.items():
      for level in sublevels:
        if query in level:
          return tier_prio
    return PrioTierEnum.IS_USELESS
  
  def cmp(self, query1, query2):
    """
    q1 < q2 => return negative
    q1 = q2 => return 0
    q1 > q2 => return positive
    """ 
    prio1 = self.get_priority_tier(query1)
    prio2 = self.get_priority_tier(query2)
    if prio1 != prio2:
      return prio2.value - prio1.value
    else:
      sublevels = self._priorities[prio1]
      index1, index2 = None, None
      for i, sublevel in enumerate(sublevels):
        if query1 in sublevel:
          index1 = i
        if query2 in sublevel: 
          index2 = i
      return index2 - index1

  def is_better(self, query1, query2):
    """is query1 better than query2?"""
    return self.cmp(query1, query2) > 0

  def is_equiv(self, query1, query2):
    return self.cmp(query1, query2) == 0