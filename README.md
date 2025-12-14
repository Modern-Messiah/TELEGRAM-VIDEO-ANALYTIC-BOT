# 🤖 Telegram Video Analytics Bot

Telegram-бот для аналитики по видео на основе запросов на естественном языке. Бот использует GPT-4 для преобразования вопросов на русском языке в SQL-запросы.

## 📋 Описание

Бот умеет отвечать на вопросы о статистике видео, используя OpenAI GPT для преобразования естественного языка в SQL-запросы к PostgreSQL базе данных.

**Telegram бот:** [@rlt_video_stats_bot](https://t.me/rlt_video_stats_bot)

### Примеры запросов:

- Сколько всего видео?
- Сколько видео набрало больше 100000 просмотров?
- На сколько просмотров выросли все видео 28 ноября 2025?
- Сколько видео получали новые просмотры 27 ноября 2025?
- Сколько видео у креатора с id XXX?
- Сколько видео вышло с 1 по 30 ноября 2025?

## Архитектура

```
┌─────────────┐
│  Telegram   │
│   User      │
└──────┬──────┘
       │ (вопрос на русском)
       ▼
┌─────────────┐      ┌──────────────┐
│  Telegram   │─────▶│   OpenAI     │
│    Bot      │      │   GPT-4o     │
│  (aiogram)  │      │              │
└──────┬──────┘      └──────┬───────┘
       │                    │
       │              (генерирует SQL)
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│ PostgreSQL  │◀─────│ SQL Query   │
│  Database   │      └─────────────┘
└─────────────┘
       │
       ▼
   (результат: число)
```

### Компоненты:

- **bot.py** - Telegram бот (aiogram 3.7.0)
- **llm_handler.py** - Обработка естественного языка через OpenAI API
- **database.py** - Работа с PostgreSQL
- **loader.py** - Загрузка JSON данных в БД
- **schema.sql** - Схема базы данных

## Структура базы данных

### Таблица `videos` (итоговая статистика):
```sql
CREATE TABLE videos (
    id VARCHAR(255) PRIMARY KEY,
    creator_id VARCHAR(255) NOT NULL,
    video_created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    reports_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
```

### Таблица `video_snapshots` (почасовые замеры):
```sql
CREATE TABLE video_snapshots (
    id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    reports_count INTEGER DEFAULT 0,
    delta_views_count INTEGER DEFAULT 0,
    delta_likes_count INTEGER DEFAULT 0,
    delta_comments_count INTEGER DEFAULT 0,
    delta_reports_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
```

## Подход к обработке естественного языка

Используется **Text-to-SQL** подход через OpenAI GPT-4o-mini:

### Промпт для LLM:

Модели предоставляется подробное описание схемы БД с правилами:

1. **Для вопросов об общем количестве видео** → используется таблица `videos`
2. **Для вопросов о датах публикации** → поле `video_created_at` из `videos`
3. **Для вопросов о приростах и динамике** → таблица `video_snapshots` с полями `delta_*`

**Пример промпта:**
```
Ты SQL-генератор для PostgreSQL базы данных с видео-аналитикой.

СТРУКТУРА БД:
1. Таблица videos (итоговая статистика)
   - id, creator_id, video_created_at
   - views_count, likes_count, comments_count, reports_count

2. Таблица video_snapshots (почасовые замеры)
   - video_id (ссылка на videos.id)
   - delta_views_count, delta_likes_count (приросты)
   - created_at (время замера)

ПРАВИЛА:
- Для подсчета видео → SELECT COUNT(*) FROM videos
- Для приростов → SELECT SUM(delta_*) FROM video_snapshots
- Для дат → WHERE DATE(created_at) = 'YYYY-MM-DD'
- Всегда используй COALESCE(..., 0)
```

### Преимущества подхода:

- Не галлюцинирует на небольших объемах данных  
- Детерминированный результат (temperature=0)  
- Прозрачность - виден сгенерированный SQL  
- Легко отлаживать и модифицировать  

## Быстрый старт (Docker)

### Требования:
- Docker
- Docker Compose
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

### Шаг 1: Клонирование

```bash
git clone https://github.com/yourusername/telegram-video-analytics-bot.git
cd telegram-video-analytics-bot
```

### Шаг 2: Настройка переменных окружения

Создайте `.env` файл:

```bash
cp .env.example .env
```

Заполните `.env`:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Шаг 3: Добавьте данные

Поместите файл `data.json` в корень проекта.

### Шаг 4: Запуск

```bash
docker-compose up -d
```

Бот автоматически:
1. Создаст базу PostgreSQL
2. Применит схему из `schema.sql`
3. Загрузит данные из `data.json`
4. Запустит Telegram бота

### Просмотр логов:

```bash
docker-compose logs -f bot
```

### Остановка:

```bash
docker-compose down
```

## Локальный запуск (без Docker)

### Требования:
- Python 3.11+
- PostgreSQL 15+

### Установка:

```bash
# Клонирование
git clone https://github.com/yourusername/telegram-video-analytics-bot.git
cd telegram-video-analytics-bot

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Зависимости
pip install -r requirements.txt

# Создание БД
createdb video_analytics
psql video_analytics < schema.sql

# Загрузка данных
python loader.py data.json

# Настройка .env
cp .env.example .env
# Отредактируйте .env

# Запуск
python bot.py
```

## Структура проекта

```
telegram-video-analytics-bot/
├── bot.py                 # Основной Telegram бот
├── llm_handler.py         # LLM обработка запросов
├── database.py            # Работа с PostgreSQL
├── loader.py              # Загрузка JSON в БД
├── test_db.py             # Тесты БД
├── schema.sql             # SQL схема
├── requirements.txt       # Python зависимости
├── .env.example           # Пример конфигурации
├── Dockerfile             # Docker образ
├── docker-compose.yml     # Docker Compose конфиг
├── entrypoint.sh          # Скрипт запуска
└── README.md              # Документация
```

## Тестирование

Примеры команд боту:

```
Сколько всего видео?
→ 358

Сколько видео набрало больше 100000 просмотров?
→ 5

На сколько просмотров выросли все видео 28 ноября 2025?
→ 14639

Сколько видео получали новые просмотры 27 ноября 2025?
→ (подсчитает уникальные video_id с delta_views_count > 0)
```

## Технологии

- **Python 3.11**
- **aiogram 3.7.0** - асинхронный Telegram Bot фреймворк
- **PostgreSQL 15** - база данных
- **OpenAI GPT-4o-mini** - обработка естественного языка
- **Docker & Docker Compose** - контейнеризация

## Логи

Все запросы логируются в формате:

```
Получен вопрос от @username: Сколько всего видео?
Вопрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos
Результат: 358
Ответ отправлен: 358
```

## Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | `123456:ABC-DEF...` |
| `OPENAI_API_KEY` | API ключ OpenAI | `sk-proj-...` |
| `DB_HOST` | Хост PostgreSQL | `postgres` |
| `DB_PORT` | Порт PostgreSQL | `5432` |
| `DB_NAME` | Имя базы данных | `video_analytics` |
| `DB_USER` | Пользователь БД | `postgres` |
| `DB_PASSWORD` | Пароль БД | `postgres` |

## Отладка

```bash
# Подключение к контейнеру бота
docker exec -it video_analytics_bot bash

# Проверка БД
docker exec -it video_analytics_db psql -U postgres -d video_analytics

# Логи в реальном времени
docker-compose logs -f

# Перезапуск бота
docker-compose restart bot
```

## 📄 Лицензия

MIT

---

**Примечание:** Для работы требуются действительные токены Telegram Bot и OpenAI API.
