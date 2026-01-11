"""Модуль для работы с Yandex GPT API."""

import requests
from pathlib import Path
from typing import Optional

from docx import Document

from utils.logging_config import get_logger
from config import YANDEX_API_KEY, YANDEX_FOLDER_ID


logger = get_logger(__name__)


def load_text_file(file_path: Path) -> Optional[str]:
    """Загружает текстовый файл."""
    try:
        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            return None
    
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            logger.debug(f"Загружен файл: {file_path}")
            return content
    
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
        return None


def load_docx_file(file_path: Path) -> Optional[str]:
    """Загружает текст из .docx файла."""
    try:
        if not file_path.exists():
            logger.error(f"Документ не найден: {file_path}")
            return None
        
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        text = '\n'.join(text_parts)
        logger.debug(f"Загружен документ: {file_path}")
        return text

    except Exception as e:
        logger.error(f"Ошибка при загрузке документа {file_path}: {e}")
        return None
    
def load_prompt() -> Optional[str]:
    """Загружает промпт из файла prompt.txt."""
    prompt_path = Path("texts") / "prompt.txt"
    return load_text_file(prompt_path)


def load_resume() -> Optional[str]:
    """Загружает описание резюме из resume.docx."""
    resume_path = Path("texts") / "resume.docx"
    return load_docx_file(resume_path)


def load_preferences() -> Optional[str]:
    """Загружает описание предпочтений из preferences.docx."""
    preferences_path = Path("texts") / "preferences.docx"
    return load_docx_file(preferences_path)


def build_prompt_text(vacancy_data: str) -> Optional[str]:
    """Собирает полный промпт из всех компонентов."""
    # Загружаем все компоненты
    prompt = load_prompt()
    resume = load_resume()
    preferences = load_preferences()

    # Проверяем что все компоненты загружены
    if not all([prompt, resume, preferences]):
        missing = []
        if not prompt: missing.append("prompt.txt")
        if not resume: missing.append("resume.docx")
        if not preferences: missing.append("preferences.docx")
        
        logger.error(f"Не удалось загрузить файлы: {', '.join(missing)}")
        return None
    
    # Собираем промпт
    full_prompt = f"""{prompt}

Описание вакансии:
{vacancy_data}

Моё резюме:
{resume}

Мои предпочтения:
{preferences}
"""   
    return full_prompt


def ask_gpt(vacancy_data: str) -> Optional[str]:
    """Отправляет данные в YandexGPT для анализа вакансии."""
    # Проверяем наличие API ключей
    if not YANDEX_API_KEY:
        logger.error("API ключ Яндекс не установлен")
        return None
    
    if not YANDEX_FOLDER_ID:
        logger.error("Folder ID Яндекс не установлен")
        return None
    
    # URL API Яндекс GPT
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "x-folder-id": YANDEX_FOLDER_ID,
    }

    # Собираем промпт
    prompt_text = build_prompt_text(vacancy_data)
    if not prompt_text:
        logger.error("Не удалось собрать промпт для GPT")
        return None
    
    # Данные для запроса
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
        },
        "messages": [
            {
                "role": "system", 
                "text": "Ты опытный карьерный консультант. "
                       "Твоя задача - объективно оценить насколько данная вакансия "
                       "подходит пользователю на основе его резюме и предпочтений. "
                       "Давай развернутый анализ с конкретными аргументами."
            },
            {
                "role": "user", 
                "text": prompt_text
            },
        ]
    }

    try:
        logger.info("Отправка запроса к YandexGPT...")
        
        response = requests.post(
            url, 
            headers=headers, 
            json=data,
            timeout=30  # Таймаут 30 секунд
        )
        response.raise_for_status()

        # Парсим ответ
        json_data = response.json()

        # Извлекаем текст ответа
        result_text = json_data["result"]["alternatives"][0]["message"]["text"]

        logger.info("Успешно получен ответ от YandexGPT")
        return result_text
    
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к YandexGPT")
        return None
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к YandexGPT: {e}")
        return None
        
    except KeyError as e:
        logger.error(f"Неожиданный формат ответа от YandexGPT: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка при работе с YandexGPT: {e}")
        return None
    


