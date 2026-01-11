"""Конфигурация логирования для всего проекта."""

import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

# Флаг для предотвращения повторной настройки
_configured = False

# Константы для конфигурации
LOG_FILE = 'bot_errors.log'
MAX_BYTES = 1024 * 1024
BACKUP_COUNT = 5
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging() -> None:
    """Настраивает логирование для всего приложения.
    Гарантирует, что настройка выполняется только один раз.
    """
    global _configured

    if _configured:
        return

    # Уменьшаем логирование для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # Настраиваем ротацию лог-файлов
    file_handler = RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.ERROR)

    # Консольный хендлер для вывода в терминал
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Базовая конфигурация
    logging.basicConfig(
        level=logging.WARNING,
        format=LOG_FORMAT,
        handlers=[file_handler, console_handler]
    )

    _configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Возвращает настроенный логгер для модуля
    Использование: logger = get_logger(__name__)
    """
    setup_logging()
    return logging.getLogger(name)