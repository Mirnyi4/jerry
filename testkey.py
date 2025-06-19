import gspread
from google.oauth2.service_account import Credentials

# Путь к вашему JSON-файлу с ключом сервисного аккаунта
SERVICE_ACCOUNT_FILE = 'service_account.json'

# Название вашей Google таблицы (точно так же, как в Google Drive)
SPREADSHEET_NAME = 'Jerry KEY'

def test_google_sheets():
    try:
        # Области доступа, необходимые для работы с таблицами
        scopes = ['https://www.googleapis.com/auth/spreadsheets',
                  'https://www.googleapis.com/auth/drive']

        # Создаем Credentials из JSON-файла
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)

        # Авторизуемся через gspread клиент
        client = gspread.authorize(creds)

        print("Авторизация прошла успешно!")

        # Открываем таблицу по имени
        sheet = client.open(SPREADSHEET_NAME).sheet1

        print(f"Таблица '{SPREADSHEET_NAME}' успешно открыта.")

        # Получаем первые 5 строк для проверки чтения данных
        records = sheet.get_all_records()
        print("Первые записи из таблицы:")
        for i, record in enumerate(records[:5]):
            print(f"{i+1}: {record}")

    except Exception as e:
        print("Ошибка при работе с Google Sheets API:")
        print(e)

if __name__ == '__main__':
    test_google_sheets()
