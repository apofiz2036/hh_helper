import gspread
import requests
import logging
import json
from utils.logging_config import get_logger
from services.gpt import ask_gpt
from services.file_manager import save_and_upload

from config import (
    SPREADSHEET_URL,
    CREDS,
    SEARCH_PARAMS,
    # TODO
)

logging.getLogger("yadisk").setLevel(logging.WARNING)
logger = get_logger(__name__)


sheet = None

def init_spreadsheet():
    """Инициализирует подключение к Google Sheets"""
    global sheet
    try:
        client = gspread.authorize(CREDS)
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        sheet = spreadsheet.sheet1

        if sheet.row_count == 0:
            headers = ["ID ВАКАНСИИ",
                       "Название вакансии",
                       "Ссылка на вакансию",
                       "Ссылка на анализ",
                       "Оценка"
            ]
            sheet.append_row(headers)
        
        logger.info("Таблица инициализирована")
        return True
    except Exception as e:
        error_message = f"Ошибка при инициализации таблицы: {e}"
        print(error_message)
        logger.error(error_message)
        return False


def save_to_spreadsheet(vacancy_info, grade, doc_link):
    """Сохраняет данные вакансии в Google Sheets"""
    try:
        row = [
            vacancy_info['id'],
            vacancy_info['name'],
            vacancy_info['url'],
            doc_link if doc_link else "Нет ссылки",
            grade if grade else "Нет оценки",           
        ]
        sheet.append_row(row)
        logger.info(f"Данные вакансии '{vacancy_info['name']}' сохранены в таблицу")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении в таблицу: {e}")
        return False


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

            print(f"Анализ вакансии {vacancy_info['name']}")

            if vacancy_info.get('description'):
                vacancy_text = f"""
                    Название вакансии: {vacancy_info['name']}
                    Город: {vacancy_info['city']}
                    Зарплата: {vacancy_info['salary']}
                    Описание вакансии: {vacancy_info['description']}
                    Навыки: {', '.join(vacancy_info.get('key_skills', []))}
                """
                gpt_response = ask_gpt(vacancy_text)
                link_to_doc, grade_result = save_and_upload(gpt_response, vacancy_info['name'])

                save_to_spreadsheet(vacancy_info, grade_result, link_to_doc)
            else:
                print("⚠️ Нет описания для анализа\n")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        return []
   

def main():
    print('Начало работы')

    if not init_spreadsheet():
        print("Ошибка при инициализации таблицы")
        return
    
    print("Таблица инициализирована")
    hh_search()
    print("Работа завершена")


if __name__ == "__main__":
    main()