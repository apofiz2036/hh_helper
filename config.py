"""Конфигурация приложения для работы с Google API и Яндекс."""

import os
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

# Загружаем переменные окружения
load_dotenv()

# --- Константы для Google API ---
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]

GOOGLE_SERVICE_ACCOUNT_FILE = "service_account.json"
SPREADSHEET_URL= "https://docs.google.com/spreadsheets/d/1OYDM-k9xUs7CSykw58ZUdOJEzNSqqXvJPpqHqwxOU5A"

# Индексы колонок (начинаются с 0)
COLUMN_INDEX_1 = 0

# --- Константы для Яндекс API ---
YANDEX_DISK_TOKEN = os.getenv("YANDEX_DISK_TOKEN")
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")


def get_google_credentials() -> Credentials:
    """Создает и возвращает учетные данные Google API."""
    if not Path(GOOGLE_SERVICE_ACCOUNT_FILE).exists():
        raise FileNotFoundError(
            f"Файл сервисного аккаунта не найден: {GOOGLE_SERVICE_ACCOUNT_FILE}"
        )
    
    return Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=GOOGLE_SCOPES
    )


# Инициализируем учетные данные Google
try:
    GOOGLE_CREDENTIALS = get_google_credentials()
except FileNotFoundError as e:
    # Можно добавить логирование здесь
    GOOGLE_CREDENTIALS = None
    print(f"Внимание: {e}. Google API будет недоступен.")


# --- Параметры поиска вакансий HH.ru ---
SEARCH_PARAMS: Dict[str, Any] = {
    "text": "Python OR Аналитик OR 'Системный аналитик'",
    "per_page": 100, 
    "page": 0,
    'only_with_salary': False,
    "experience": "noExperience",  #"between1And3" - для опыта работы от 1 до 3-х лет
    "schedule": "remote", 
}


# --- Валидация конфигурации ---
def validate_config() -> bool:
    """Проверяет корректность конфигурации."""
    errors = []

    # Проверяем Яндекс токены
    if not YANDEX_DISK_TOKEN:
        errors.append("Не указан YANDEX_DISK_TOKEN в переменных окружения")
    
    if not YANDEX_API_KEY:
        errors.append("Не указан YANDEX_API_KEY в переменных окружения")
    
    if not GOOGLE_CREDENTIALS:
        errors.append("Учетные данные Google не инициализированы")
    
    if errors:
        print("Ошибки конфигурации:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# Флаг валидности конфигурации
CONFIG_VALID = validate_config()