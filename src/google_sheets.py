import json
import os
from typing import Optional

import gspread
from gspread.exceptions import APIError, SpreadsheetNotFound, WorksheetNotFound
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _load_credentials(service_account_file: Optional[str] = None) -> Credentials:
    info_env = os.getenv("GOOGLE_SERVICE_ACCOUNT_INFO")
    if info_env:
        info = json.loads(info_env)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    file_path = service_account_file or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Service account credentials not found. Provide GOOGLE_SERVICE_ACCOUNT_INFO or a file at {file_path}"
        )
    return Credentials.from_service_account_file(file_path, scopes=SCOPES)


def get_client(service_account_file: Optional[str] = None) -> gspread.Client:
    creds = _load_credentials(service_account_file)
    return gspread.authorize(creds)


def open_sheet(spreadsheet_name: str, worksheet_name: str):
    """Open or create a worksheet by name.

    Returns (spreadsheet, worksheet)
    """
    client = get_client()
    try:
        sh = client.open(spreadsheet_name)
    except SpreadsheetNotFound:
        try:
            sh = client.create(spreadsheet_name)
        except APIError as err:
            raise RuntimeError(
                f"Spreadsheet '{spreadsheet_name}' was not found and could not be created. "
                "The authenticated Google Drive account may be over quota or lack permission to create spreadsheets."
            ) from err

    try:
        ws = sh.worksheet(worksheet_name)
    except WorksheetNotFound:
        try:
            ws = sh.add_worksheet(title=worksheet_name, rows=1000, cols=10)
        except APIError as err:
            raise RuntimeError(
                f"Worksheet '{worksheet_name}' could not be created inside '{spreadsheet_name}'. "
                "Free space in Google Drive or create the worksheet manually, then rerun the scraper."
            ) from err

    return sh, ws


def ensure_headers(ws, headers):
    current = ws.row_values(1)
    if current == headers:
        return
    if not current:
        ws.update([headers])
        return
    # If headers exist but differ, overwrite first row with our expected headers
    ws.update("A1", [headers])
