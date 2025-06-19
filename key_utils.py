import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

GOOGLE_KEYFILE = "service_account.json"
SHEET_NAME = "Jerry KEY"  # Название твоей Google Таблицы

def get_keys_from_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_KEYFILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    return sheet.get_all_records()

def is_key_valid(entered_key):
    records = get_keys_from_google_sheet()
    for row in records:
        key = str(row.get("Ключ", "")).strip()
        paid = str(row.get("Оплачен", "")).strip().lower() == "да"
        date_str = row.get("Дата активации", "")
        try:
            activated_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else None
        except:
            activated_at = None

        if key == entered_key:
            if paid:
                return True
            if activated_at and (datetime.now() - activated_at).days <= 30:
                return True
            return False
    return False
