from database import execute_query, get_table_stats, test_connection

print("=" * 60)
print("  ПРОВЕРКА БАЗЫ ДАННЫХ")
print("=" * 60)

# Тест подключения
test_connection()

# Статистика
print("\n📊 Статистика:")
get_table_stats()

# Пример запросов
print("\n🔍 Примеры запросов:")

# Всего видео
total = execute_query("SELECT COUNT(*) FROM videos")
print(f"  Всего видео: {total}")

# Видео с просмотрами > 1000
popular = execute_query("SELECT COUNT(*) FROM videos WHERE views_count > 1000")
print(f"  Видео с >1000 просмотров: {popular}")

# Разные креаторы
creators = execute_query("SELECT COUNT(DISTINCT creator_id) FROM videos")
print(f"  Уникальных креаторов: {creators}")

print("\nВсё работает!")
print("=" * 60)
