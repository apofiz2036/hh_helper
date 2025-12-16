import logging
from logging.handlers import RotatingFileHandler

_configured = False

def setup_logging():
    global _configured
    if _configured:
        return

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    file_handler = RotatingFileHandler(
        'bot_errors.log',
        maxBytes=1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.ERROR)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )


def get_logger(name=None):
    """
    Возвращает настроенный логгер для модуля
    Использование: logger = get_logger(__name__)
    """
    setup_logging()
    return logging.getLogger(name)