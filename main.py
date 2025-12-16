import gspread
from utils.logging_config import get_logger

from config import (
    SPREADSHEET_URL,
    CREDS,
    # TODO
)

logger = get_logger(__name__)

def main():
    print('Начало работы')

    #  Авторизация В GOOGLE SHEETS
    try:
        client = gspread.authorize(CREDS)
        print("Авторизация успешна")
    except Exception as e:
        error_message = f"Ошибка авторизации: {e}"
        print(error_message)
        logger.error(error_message)
        return
    
    # Открытие таблицы
    try:
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        sheet = spreadsheet.sheet1
    except Exception as e:
        error_message = f"Ошибка при открытии таблицы: {e}"
        print(error_message)
        logger.error(error_message)
        return
    
    # Получение данных из таблицы
    data_from_sheet = sheet.get_all_values()
    headers = data_from_sheet[0]

    sheet.update_cell(1, 1, 'Hello World')


if __name__ == "__main__":
    main()