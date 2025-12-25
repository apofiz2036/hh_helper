import gspread
import requests
import json
import pprint
from utils.logging_config import get_logger

from config import (
    SPREADSHEET_URL,
    CREDS,
    SEARCH_PARAMS,
    # TODO
)

logger = get_logger(__name__)


def get_vacancy_details(vacancy_id):
    try:
        response = requests.get(
            f'https://api.hh.ru/vacancies/{vacancy_id}',
            headers={'User-Agent': 'MyVacancyParser/1.0 (apofiz2036@bk.ru)'}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе деталей вакансии {vacancy_id}: {e}")
        return None


def hh_search():
    try:
        response = requests.get(
            'https://api.hh.ru/vacancies',
            params=SEARCH_PARAMS,
            headers={
                'User-Agent': 'MyVacancyParser/1.0 (apofiz2036@bk.ru)'
            }
        )

        response.raise_for_status()
        data = response.json()

        vacancies_list = []

        for item in data['items']:
            vacancy_info = {
                'id': item['id'],
                'name': item['name'],
                'city': item['area']['name'],
                'salary': item.get('salary'),
                'url': item['alternate_url'],
            }

            details = get_vacancy_details(item['id'])
            if details:
                vacancy_info['description'] = details.get('description', '')
                vacancy_info['key_skills'] = [skill['name'] for skill in details.get('key_skills', [])]

            vacancies_list.append(vacancy_info)

        pprint.pprint(vacancies_list)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return []
   

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

    # TODO
    hh_search()

    sheet.update_cell(1, 1, 'Hello World')


if __name__ == "__main__":
    main()