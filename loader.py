import json
from datetime import datetime

import psycopg2

from database import DB_CONFIG


def load_json_to_database(json_file_path: str):
    """
    Загружает данные из JSON файла в PostgreSQL базу данных

    Args:
        json_file_path: Путь к JSON файлу с данными
    """
    print(f"🔄 Начинаем загрузку данных из {json_file_path}...")

    # Читаем JSON файл
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {json_file_path} не найден!")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return

    videos = data.get("videos", [])
    print(f"📦 Найдено {len(videos)} видео для загрузки")

    # Подключаемся к БД
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    videos_loaded = 0
    snapshots_loaded = 0

    try:
        for idx, video in enumerate(videos, 1):
            # Вставляем видео
            cur.execute(
                """
                INSERT INTO videos (
                    id, creator_id, video_created_at,
                    views_count, likes_count, comments_count, reports_count,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    views_count = EXCLUDED.views_count,
                    likes_count = EXCLUDED.likes_count,
                    comments_count = EXCLUDED.comments_count,
                    reports_count = EXCLUDED.reports_count,
                    updated_at = EXCLUDED.updated_at
            """,
                (
                    video["id"],
                    video["creator_id"],
                    video["video_created_at"],
                    video.get("views_count", 0),
                    video.get("likes_count", 0),
                    video.get("comments_count", 0),
                    video.get("reports_count", 0),
                    video.get("created_at"),
                    video.get("updated_at"),
                ),
            )
            videos_loaded += 1

            # Вставляем снапшоты
            snapshots = video.get("snapshots", [])
            for snapshot in snapshots:
                cur.execute(
                    """
                    INSERT INTO video_snapshots (
                        id, video_id,
                        views_count, likes_count, comments_count, reports_count,
                        delta_views_count, delta_likes_count,
                        delta_comments_count, delta_reports_count,
                        created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """,
                    (
                        snapshot["id"],
                        snapshot["video_id"],
                        snapshot.get("views_count", 0),
                        snapshot.get("likes_count", 0),
                        snapshot.get("comments_count", 0),
                        snapshot.get("reports_count", 0),
                        snapshot.get("delta_views_count", 0),
                        snapshot.get("delta_likes_count", 0),
                        snapshot.get("delta_comments_count", 0),
                        snapshot.get("delta_reports_count", 0),
                        snapshot.get("created_at"),
                        snapshot.get("updated_at"),
                    ),
                )
                snapshots_loaded += 1

            # Прогресс каждые 100 видео
            if idx % 100 == 0:
                print(f"  Обработано {idx}/{len(videos)} видео...")
                conn.commit()

        conn.commit()
        print(f"\n Загрузка завершена успешно!")
        print(f"   Загружено видео: {videos_loaded}")
        print(f"   Загружено снапшотов: {snapshots_loaded}")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Ошибка при загрузке: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import sys

    # Путь к JSON файлу
    json_path = sys.argv[1] if len(sys.argv) > 1 else "data.json"

    print("=" * 60)
    print("  ЗАГРУЗКА ДАННЫХ В БАЗУ")
    print("=" * 60)

    load_json_to_database(json_path)
