# Анализатор вакансии на сайте HH.ru 

Проект для автоматического поиска, анализа и сохранения вакансий с HeadHunter (HH.ru) с использованием Yandex GPT для оценки релевантности.

## Возможности

- **Поиск вакансий** на HH.ru по заданным критериям
- **AI-анализ** каждой вакансии с использованием Yandex GPT
- **Автоматическая оценка** релевантности вакансии ( в формате 0/10)
- **Создание документов** с детальным анализом каждой вакансии
- **Загрузка на Яндекс Диск** для постоянного доступа
- **Экспорт в Google Sheets** с результатами анализа

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone <ваш-репозиторий>
cd hh_helper
```

### 2. Создание виртуального окружения

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации

#### 4.1 Google API
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Google Sheets API
3. Создайте сервисный аккаунт
4. Скачайте JSON ключ и сохраните как `service_account.json` в корне проекта
5. Предоставьте доступ к вашей Google таблице по email сервисного аккаунта

#### 4.2 Яндекс API
1. Получите токен Яндекс Диска в [Яндекс OAuth](https://oauth.yandex.ru/)
2. Получите API ключ для Yandex GPT в [Yandex Cloud](https://cloud.yandex.ru/)
3. Создайте `.env` файл в корне проекта:

```env
YANDEX_DISK_TOKEN=ваш_токен_яндекс_диска
YANDEX_API_KEY=ваш_api_ключ_yandex_gpt
YANDEX_FOLDER_ID=ваш_folder_id_yandex_cloud
```

#### 4.3 Текстовые файлы
Создайте папку `texts/` и добавьте:
- `prompt.txt` - инструкции для GPT анализа
- `resume.docx` - ваше резюме
- `preferences.docx` - ваши предпочтения по работе

## Структура проекта

```
hh_helper/
├── main.py                    # Основной скрипт
├── config.py                  # Конфигурация приложения
├── requirements.txt           # Зависимости Python
├── .env                       # Переменные окружения
├── service_account.json       # Ключи Google API
├── texts/                     # Текстовые файлы для GPT
│   ├── prompt.txt
│   ├── resume.docx
│   └── preferences.docx
├── utils/
│   └── logging_config.py     # Конфигурация логирования
├── services/
│   ├── gpt.py                # Работа с Yandex GPT
│   └── file_manager.py       # Работа с файлами и Яндекс Диском
├── output_docs/              # Автоматически создаваемые документы
└── bot_errors.log           # Файл логов ошибок
```

## Конфигурация

Основные настройки в `config.py`:

```python
# Параметры поиска вакансий
SEARCH_PARAMS = {
    "text": "Python OR Аналитик OR 'Системный аналитик'",
    "per_page": 100,
    "page": 0,
    'only_with_salary': False,
    "experience": "noExperience",  # Без опыта
    "schedule": "remote",         # Удаленная работа
}
```

**Доступные параметры поиска:**
- `text`: Ключевые слова
- `experience`: Уровень опыта (noExperience, between1And3, etc.)
- `schedule`: График работы (remote, fullDay, flexible)
- `area`: Регион поиска

## Использование

### Базовый запуск

```bash
python main.py
```
### Запуск через batch-файл (Windows)

Используйте готовый скрипт для автоматизации
```bash
RUN_hh_helper.bat
```

Файл RUN_hh_helper.bat автоматически:
1. Устанавливает правильную кодировку консоли
2. Активирует виртуальное окружение
3. Запускает основной скрипт
4. Ожидает нажатия клавиши перед закрытием

### Процесс работы

1. **Инициализация** таблицы Google Sheets
2. **Поиск вакансий** на HH.ru (первые 5 страниц)
3. **Фильтрация** уже обработанных вакансий
4. **Анализ каждой вакансии** через Yandex GPT
5. **Создание документа** с анализом
6. **Загрузка на Яндекс Диск**
7. **Сохранение результатов** в Google Sheets

## 📝 Логирование

Приложение использует многоуровневое логирование:

- **Консоль**: WARNING и выше
- **Файл `bot_errors.log`**: Только ERROR с ротацией (1MB, 5 файлов)
- **Отключенные логи**: httpx, apscheduler, yadisk (уровень WARNING)

Пример использования в коде:
```python
from utils.logging_config import get_logger
logger = get_logger(__name__)
logger.info("Сообщение")
```
