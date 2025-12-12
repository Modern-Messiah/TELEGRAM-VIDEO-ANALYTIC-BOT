import os
import time
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "video_analytics"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def wait_for_db(max_retries=30, delay=2):
    """Ждём пока база данных станет доступна"""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            return True
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"Ожидание БД... попытка {i + 1}/{max_retries}")
                time.sleep(delay)
            else:
                return False
    return False


@contextmanager
def get_db_connection():
    # Context manager для безопасной работы с БД
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def execute_query(sql: str, params: tuple = None) -> any:
    """
    Выполняет SQL запрос и возвращает результат

    Args:
        sql: SQL запрос
        params: Параметры для запроса (опционально)

    Returns:
        Результат запроса (обычно одно число)
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                result = cur.fetchone()

                if result:
                    # Получаем первое значение из результата
                    first_value = list(result.values())[0]
                    return first_value if first_value is not None else 0
                return 0
    except Exception as e:
        print(f"❌ Ошибка выполнения SQL: {e}")
        print(f"   SQL: {sql}")
        raise


def test_connection():
    # Проверка подключения к БД
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print("Подключение к базе данных успешно!")
                return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False


def get_table_stats():
    """Получение статистики по таблицам"""
    try:
        videos_count = execute_query("SELECT COUNT(*) FROM videos")
        snapshots_count = execute_query("SELECT COUNT(*) FROM video_snapshots")
        print(f"Видео в БД: {videos_count}")
        print(f"Снапшотов в БД: {snapshots_count}")
        return videos_count, snapshots_count
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return 0, 0
