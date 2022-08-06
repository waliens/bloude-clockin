
import datetime
from discord import InvalidArgument


def default_if_none(v, d=None):
  return d if v is None else v


def get_applied_user_id(ctx, for_user, user_id):
  """return the id to which the query should be applied"""
  if for_user is None:
    return user_id

  if user_id != str(for_user.id) and not ctx.author.guild_permissions.administrator:
    raise InvalidArgument("you do not have the permissions to execute this command on behalf of another user")

  return str(for_user.id)


def parse_date(date_str, default=None):
  try:
    if date_str is None:
      return default
    return datetime.datetime.strptime(date_str, '%d/%m/%Y').date()
  except ValueError:
    raise InvalidArgument("cannot parse date, should be in format DD/MM/YYYY")


def parse_datetime(datetime_str, default=None):
  try:
    if datetime_str is None:
      return default
    return datetime.datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
  except ValueError:
    raise InvalidArgument("cannot parse date, should be in format DD/MM/YYYY HH:mm")
