import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetStateEnum():
  OK = 1
  UNKNOWN_SHEET = 2
  INVALID_PERMS = 3


def get_creds():
  GSHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
  prefix = "GOOGLE_API_"
  info = {k.replace(prefix, "").lower(): v.replace("\\n", "\n") for k, v in os.environ.items() if k.startswith(prefix)}
  return service_account.Credentials.from_service_account_info(info, scopes=GSHEET_SCOPES)


def get_service_name():
  return os.environ["GOOGLE_API_PROJECT_ID"]


def make_bot_guser_name():
  sname = get_service_name()
  return f"{sname}@{sname}.iam.gserviceaccount.com"
  

def get_sheet_service():
  return build('sheets', 'v4', credentials=get_creds())


def check_sheet(id_gsheet):
  try: 
    gsheet = get_sheet_service().spreadsheets()
    gsheet.values().get(spreadsheetId=id_gsheet, range="A1").execute()
    return SheetStateEnum.OK
  except HttpError as e:
    if e.status_code == 404:
      return SheetStateEnum.UNKNOWN_SHEET
    elif e.status_code == 403:
      return SheetStateEnum.INVALID_PERMS
    raise e
