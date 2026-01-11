"""Модуль для работы с документами и Яндекс Диском."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from docx import Document
from yadisk import YaDisk

from utils.logging_config import get_logger
from config import YANDEX_DISK_TOKEN

logger = get_logger(__name__)


def clean_filename(filename: str) -> str:
    """Очищает имя файла от запрещенных символов."""
    # Заменяем запрещенные символы на подчеркивание
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Заменяем множественные пробелы на одно подчеркивание
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Убираем пробелы в начале и конце
    return cleaned.strip('_')


def extract_grade(file_path: str) -> Optional[str]:
    """
    Извлекает оценку из последней строки Word документа
    Ожидает формат: '8/10' или '8 / 10'
    """
    try:
        doc = Document(file_path)

        # Проверяем, что в документе есть параграфы
        if not doc.paragraphs:
            logger.warning(f"Документ {file_path} пуст")
            return None
        
        # Берем текст последнего параграфа
        last_paragraph = doc.paragraphs[-1]
        last_line = last_paragraph.text.strip()

        if not last_line:
            logger.warning(f"Последняя строка документа {file_path} пуста")
            return None
        
        # Ищем оценку в формате "число/10"
        # Регулярное выражение ищет: число, затем пробелы (или нет), затем /, затем пробелы (или нет), затем 10
        match = re.search(r'(\d+)\s*/\s*10', last_line)

        if match:
            grade = match.group(0)
            logger.info(f"Извлечена оценка {grade} из {file_path}")
            return grade
        
        logger.warning(f"Оценка не найдена в последней строке: '{last_line}'")
        return None
    
    except Exception as e:
        error_message = f"Ошибка при извлечении оценки из {file_path}: {e}"
        logger.error(error_message)
        return None


def save_docx(text: str, name: str) -> Optional[str]:
    """Сохраняет текст в Word документ на локальный диск"""
    try:
        # Создаем директорию для документов
        output_dir = Path("output_docs")
        output_dir.mkdir(exist_ok=True)

        # Очищаем имя вакансии для использования в имени файла
        safe_name = clean_filename(name)

        # Добавляем timestamp для уникальности
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.docx"
        file_path = output_dir / filename

        # Создаем документ
        doc = Document()

        # Добавляем текст (можно разделить на параграфы при необходимости)
        doc.add_paragraph(text)

        # Сохраняем
        doc.save(str(file_path))

        logger.info(f"Документ сохранен: {file_path}")
        return str(file_path)
    
    except Exception as e:
        error_message = f"Ошибка при сохранении документа '{name}': {e}"
        logger.error(error_message)
        return None
    

def upload_to_yandex(file_path: str) -> Optional[str]:
    """Загружает файл на Яндекс Диск и возвращает публичную ссылку"""
    try:
        # Проверяем наличие токена
        if not YANDEX_DISK_TOKEN:
            logger.error("Токен Яндекс Диска не установлен")
            return None

        # Проверяем существование файла
        if not Path(file_path).exists():
            logger.error(f"Файл не найден: {file_path}")
            return None
        
        # Инициализируем клиент Яндекс Диска
        yandex = YaDisk(token=YANDEX_DISK_TOKEN)

        # Директория на Яндекс Диске
        remote_dir = "/vacancy_script"

        # Создаем папку если её нет
        if not yandex.exists(remote_dir):
            yandex.mkdir(remote_dir)
            logger.info(f"Создана директория на Яндекс Диске: {remote_dir}")

        # Формируем путь на Яндекс Диске
        filename = Path(file_path).name
        remote_path = f"{remote_dir}/{filename}"

        # Загружаем файл
        yandex.upload(file_path, remote_path, overwrite=True)
        logger.info(f"Файл загружен на Яндекс Диск: {remote_path}")

        # Получаем публичную ссылку
        public_link = yandex.get_download_link(remote_path)

        return public_link
    
    except Exception as e:
        error_message = f"Ошибка при загрузке на Яндекс Диск {file_path}: {e}"
        logger.error(error_message)
        return None


def save_and_upload(text: str, name: str) -> Tuple[Optional[str], Optional[str]]:
    """Основная функция: сохраняет текст в DOCX и загружает на Яндекс Диск"""
    try:
        # Сохраняем локально
        file_path = save_docx(text, name)
        if not file_path:
            logger.error(f"Не удалось сохранить документ для вакансии '{name}'")
            return None, None
        
        # Загружаем на Яндекс Диск
        link = upload_to_yandex(file_path)
        if not link:
            logger.warning(f"Не удалось загрузить документ на Яндекс Диск: {file_path}")
        
        # Извлекаем оценку
        grade = extract_grade(file_path)

        logger.info(f"Обработан документ '{name}': ссылка={'есть' if link else 'нет'}, оценка={grade or 'нет'}")

        return link, grade
    
    except Exception as e:
        error_message = f"Ошибка при обработке документа для вакансии '{name}': {e}"
        logger.error(error_message)
        return None, None
