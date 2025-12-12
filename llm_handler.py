import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from database import execute_query

load_dotenv()

# Инициализация OpenAI клиента
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Промпт с описанием схемы БД
SYSTEM_PROMPT = """Ты SQL-генератор для PostgreSQL базы данных с видео-аналитикой.

СТРУКТУРА БД:

1. Таблица `videos` (итоговая статистика по каждому видео):
   - id (VARCHAR): уникальный идентификатор видео
   - creator_id (VARCHAR): идентификатор создателя видео
   - video_created_at (TIMESTAMP WITH TIME ZONE): дата и время публикации видео
   - views_count (INTEGER): финальное количество просмотров
   - likes_count (INTEGER): финальное количество лайков
   - comments_count (INTEGER): финальное количество комментариев
   - reports_count (INTEGER): финальное количество жалоб
   - created_at (TIMESTAMP WITH TIME ZONE): дата добавления в систему
   - updated_at (TIMESTAMP WITH TIME ZONE): дата последнего обновления

2. Таблица `video_snapshots` (почасовые замеры статистики):
   - id (VARCHAR): уникальный идентификатор снапшота
   - video_id (VARCHAR): ссылка на videos.id
   - views_count (INTEGER): количество просмотров на момент замера
   - likes_count (INTEGER): количество лайков на момент замера
   - comments_count (INTEGER): количество комментариев на момент замера
   - reports_count (INTEGER): количество жалоб на момент замера
   - delta_views_count (INTEGER): прирост просмотров с прошлого замера
   - delta_likes_count (INTEGER): прирост лайков с прошлого замера
   - delta_comments_count (INTEGER): прирост комментариев с прошлого замера
   - delta_reports_count (INTEGER): прирост жалоб с прошлого замера
   - created_at (TIMESTAMP WITH TIME ZONE): время замера (примерно раз в час)
   - updated_at (TIMESTAMP WITH TIME ZONE): время последнего обновления

ПРАВИЛА ГЕНЕРАЦИИ SQL:

1. **Для вопросов об общем количестве видео** используй таблицу `videos`:
   - "Сколько всего видео?" → SELECT COUNT(*) FROM videos
   - "Сколько видео набрало больше X просмотров?" → SELECT COUNT(*) FROM videos WHERE views_count > X

2. **Для вопросов о креаторах** используй таблицу `videos`:
   - "Сколько видео у креатора X?" → SELECT COUNT(*) FROM videos WHERE creator_id = 'X'

3. **Для вопросов о датах публикации видео** используй поле `video_created_at` из таблицы `videos`:
   - "Сколько видео вышло 1 ноября 2025?" → SELECT COUNT(*) FROM videos WHERE DATE(video_created_at) = '2025-11-01'
   - "Сколько видео с 1 по 5 ноября?" → SELECT COUNT(*) FROM videos WHERE video_created_at BETWEEN '2025-11-01' AND '2025-11-05 23:59:59'

4. **Для вопросов о приростах и динамике** используй таблицу `video_snapshots`:
   - "На сколько просмотров выросли все видео 28 ноября?" → SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = '2025-11-28'
   - "Сколько видео получали новые просмотры 27 ноября?" → SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '2025-11-27' AND delta_views_count > 0

5. **ВАЖНО**:
   - Всегда используй COALESCE(..., 0) чтобы NULL превращался в 0
   - Для дат используй DATE() функцию для сравнения только даты без времени
   - Для диапазонов дат используй BETWEEN с включением конечной даты (добавь 23:59:59)
   - Даты пиши в формате 'YYYY-MM-DD'
   - Месяцы на русском: январь=01, февраль=02, март=03, апрель=04, май=05, июнь=06, июль=07, август=08, сентябрь=09, октябрь=10, ноябрь=11, декабрь=12

6. **Формат ответа**:
   - Верни ТОЛЬКО SQL запрос, без объяснений
   - Запрос должен возвращать ОДНО ЧИСЛО
   - Не добавляй markdown форматирование (```sql)
   - Не добавляй точку с запятой в конце

ПРИМЕРЫ:

Вопрос: "Сколько всего видео?"
Ответ: SELECT COUNT(*) FROM videos

Вопрос: "Сколько видео набрало больше 100000 просмотров?"
Ответ: SELECT COUNT(*) FROM videos WHERE views_count > 100000

Вопрос: "На сколько просмотров выросли все видео 28 ноября 2025?"
Ответ: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE DATE(created_at) = '2025-11-28'

Вопрос: "Сколько видео получали просмотры 27 ноября 2025?"
Ответ: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE DATE(created_at) = '2025-11-27' AND delta_views_count > 0
"""


async def process_natural_language_query(question: str) -> int:
    """
    Обрабатывает вопрос на естественном языке и возвращает числовой результат

    Args:
        question: Вопрос пользователя на русском языке

    Returns:
        Числовой результат запроса
    """
    import sys

    print(f"\nВопрос: {question}", flush=True)
    sys.stdout.flush()

    # Генерируем SQL через GPT
    response = await client.chat.completions.create(
        model="gpt-4o-mini",  # Используем mini версию - быстрее и дешевле
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,  # Делаем ответ более детерминированным
    )

    sql_query = response.choices[0].message.content.strip()

    # Убираем markdown если есть
    if sql_query.startswith("```sql"):
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    elif sql_query.startswith("```"):
        sql_query = sql_query.replace("```", "").strip()

    # Убираем точку с запятой в конце
    sql_query = sql_query.rstrip(";")

    print(f"🔍 SQL: {sql_query}", flush=True)
    sys.stdout.flush()

    # Выполняем запрос
    try:
        result = execute_query(sql_query)
        print(f"Результат: {result}", flush=True)
        sys.stdout.flush()
        return result
    except Exception as e:
        print(f"❌ Ошибка выполнения SQL: {e}", flush=True)
        sys.stdout.flush()
        raise
