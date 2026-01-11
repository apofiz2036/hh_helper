"""Основной модуль для поиска и анализа вакансий с HH.ru."""

import time
import json
from typing import Dict, List, Optional, Any, Tuple

import gspread
import requests
import logging

from utils.logging_config import get_logger
from services.gpt import ask_gpt
from services.file_manager import save_and_upload

from config import (
    SPREADSHEET_URL,
    GOOGLE_CREDENTIALS as CREDS,
    SEARCH_PARAMS,
    CONFIG_VALID
)


# Настраиваем логирование
logging.getLogger("yadisk").setLevel(logging.WARNING)
logger = get_logger(__name__)

# Глобальная переменная для таблицы
_sheet: Optional[gspread.Worksheet] = None


def init_spreadsheet() -> bool:
    """Инициализирует подключение к Google Sheets"""
    global _sheet

    try:
        # Проверяем валидность конфигурации
        if not CONFIG_VALID:
            logger.error("Конфигурация невалидна, инициализация таблицы невозможна")
            return False
        
        if CREDS is None:
            logger.error("Учетные данные Google не доступны")
            return False
        
        client = gspread.authorize(CREDS)
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        _sheet = spreadsheet.sheet1

        # Добавляем заголовки, если таблица пуста
        if _sheet.row_count == 0:
            headers = [
                "ID ВАКАНСИИ",
                "Название вакансии",
                "Ссылка на вакансию",
                "Ссылка на анализ",
                "Оценка"
            ]
            _sheet.append_row(headers)
            logger.info("Добавлены заголовки в таблицу")

        logger.info("Таблица инициализирована")
        return True
    
    except gspread.exceptions.APIError as e:
        error_message = f"Ошибка API Google Sheets: {e}"
        logger.error(error_message)
        print(error_message)
        return False
    except Exception as e:
        error_message = f"Ошибка при инициализации таблицы: {e}"
        print(error_message)
        logger.error(error_message)
        return False


def is_vacancy_exist(vacancy_id: str) -> bool:
    """Проверка есть ли вакансия в таблице"""
    if _sheet is None:
        logger.warning("Таблица не инициализирована")
        return False
    
    try:
        vacancy_id_str = str(vacancy_id).strip()
        # Получаем все ID из первого столбца (пропускаем заголовок)
        existing_ids = _sheet.col_values(1)[1:]

        for existing_id in existing_ids:
            if existing_id.strip() == vacancy_id_str:
                return True
        return False
    
    except Exception as e:
        logger.error(f"Ошибка при проверке существования вакансии {vacancy_id}: {e}")
        return False

    

def save_to_spreadsheet(vacancy_info: Dict[str, Any], grade: str, doc_link: str) -> bool:
    """Сохраняет данные вакансии в Google Sheets"""
    if _sheet is None:
        logger.error("Таблица не инициализирована для сохранения")
        return False

    try:
        vacancy_name = vacancy_info.get('name', 'Без названия')
        row_data = [
            str(vacancy_info.get('id', '')),
            vacancy_name,
            vacancy_info.get('url', ''),
            doc_link if doc_link else "Нет ссылки",
            grade if grade else "Нет оценки",           
        ]

        _sheet.append_row(row_data)
        logger.info(f"Вакансия '{vacancy_name}' сохранена в таблицу")
        return True
    
    except Exception as e:
        logger.error(f"Ошибка при сохранении вакансии '{vacancy_info.get('name')}' в таблицу: {e}")
        return False


def get_vacancy_details(vacancy_id: str) -> Optional[Dict[str, Any]]:
    """Получает детальную информацию о вакансии по ID."""
    try:
        url = f'https://api.hh.ru/vacancies/{vacancy_id}'
        headers = {'User-Agent': 'MyVacancyParser/1.0 (apofiz2036@bk.ru)'}

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при запросе деталей вакансии {vacancy_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе деталей вакансии {vacancy_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON для вакансии {vacancy_id}: {e}")
        return None


def extract_vacancy_info(item: Dict[str, Any], details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Извлекает и структурирует информацию о вакансии."""
    vacancy_info = {
        'id': item['id'],
        'name': item['name'],
        'city': item['area']['name'],
        'salary': item.get('salary'),
        'url': item['alternate_url'],
        'description': '',
        'key_skills': []
    }

    if details:
        vacancy_info['description'] = details.get('description', '')
        vacancy_info['key_skills'] = [skill['name'] for skill in details.get('key_skills', [])]
    
    return vacancy_info


def create_vacancy_text(vacancy_info: Dict[str, Any]) -> str:
    """Создает форматированный текст вакансии для анализа GPT"""
    salary_info = vacancy_info.get('salary')
    if salary_info:
        salary_str = f"{salary_info.get('from', '')}-{salary_info.get('to', '')} {salary_info.get('currency', '')}"
    else:
        salary_str = "Не указана"
    
    skills_str = ', '.join(vacancy_info.get('key_skills', [])) or "Не указаны"

    return f"""
Название вакансии: {vacancy_info['name']}
Город: {vacancy_info['city']}
Зарплата: {salary_str}
Описание вакансии: {vacancy_info.get('description', 'Нет описания')}
Навыки: {skills_str}
"""


def search_hh_vacancies(max_pages: int = 5) -> List[Dict[str, Any]]:
    """Выполняет поиск вакансий на HH.ru."""
    all_vacancies = []
    try:
        for page in range(max_pages):
            params = SEARCH_PARAMS.copy()
            params['page'] = page
            params['per_page'] = 100

            response = requests.get(
                'https://api.hh.ru/vacancies',
                params=params,
                headers={'User-Agent': 'MyVacancyParser/1.0 (apofiz2036@bk.ru)'},
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            found = data.get('found', 0)
            pages = data.get('pages', 1)
            
            print(f"📄 Страница {page + 1}/{pages}, найдено вакансий: {found}")
            logger.info(f"Получено {len(data.get('items', []))} вакансий со страницы {page + 1}")
            
            all_vacancies.extend(data.get('items', []))
            
            # Прерываем если больше нет страниц
            if page + 1 >= pages:
                break
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при поиске вакансий: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при поиске вакансий: {e}")
    
    return all_vacancies


def process_vacancies(vacancies: List[Dict[str, Any]]) -> int:
    """Обрабатывает список вакансий."""
    processed_count = 0
    for item in vacancies:
        vacancy_id = item['id']
        
        # Пропускаем если уже обработана
        if is_vacancy_exist(vacancy_id):
            print(f"⏭️ Вакансия {vacancy_id} уже есть в таблице")
            continue
        
        # Получаем детали
        details = get_vacancy_details(vacancy_id)
        vacancy_info = extract_vacancy_info(item, details)
        
        print(f"🔍 Анализ вакансии: {vacancy_info['name']}")
        
        # Проверяем наличие описания
        if not vacancy_info.get('description'):
            print("⚠️ Нет описания для анализа\n")
            continue
        
        # Анализируем через GPT
        vacancy_text = create_vacancy_text(vacancy_info)
        gpt_response = ask_gpt(vacancy_text)
        
        # Сохраняем и загружаем результаты
        link_to_doc, grade_result = save_and_upload(gpt_response, vacancy_info['name'])
        
        # Сохраняем в таблицу
        if save_to_spreadsheet(vacancy_info, grade_result, link_to_doc):
            processed_count += 1
        
        # Пауза между запросами для соблюдения лимитов API
        time.sleep(1)

    return processed_count


def main() -> None:
    """Основная функция приложения."""
    print("🚀 Начало работы парсера вакансий")
    logger.info("Запуск парсера вакансий")

    # Инициализируем таблицу
    if not init_spreadsheet():
        print("❌ Ошибка при инициализации таблицы. Завершение работы.")
        logger.error("Не удалось инициализировать таблицу")
        return
    
    print("✅ Таблица Google Sheets инициализирована")

    # Ищем вакансии
    print("🔎 Поиск вакансий на HH.ru...")
    vacancies = search_hh_vacancies(max_pages=5)
    
    if not vacancies:
        print("⚠️ Вакансии не найдены")
        logger.warning("Не найдено вакансий по заданным параметрам")
        return
    
    print(f"📊 Найдено вакансий: {len(vacancies)}")

    # Обрабатываем вакансии
    processed_count = process_vacancies(vacancies)

    # Итоги
    print(f"\n{'='*50}")
    print(f"✅ Обработано новых вакансий: {processed_count}")
    print(f"🏁 Работа завершена")
    logger.info(f"Завершена обработка. Обработано вакансий: {processed_count}")


if __name__ == "__main__":
    main()
