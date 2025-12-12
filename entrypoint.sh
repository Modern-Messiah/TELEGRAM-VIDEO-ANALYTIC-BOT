#!/bin/bash
set -e

echo "ЗАПУСК VIDEO ANALYTICS BOT"

# Ждём когда PostgreSQL будет готов
echo "Ожидание PostgreSQL..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "PostgreSQL недоступен - ждём..."
  sleep 2
done

echo "PostgreSQL готов!"

# Проверяем есть ли данные в БД
echo ""
echo "Проверка данных в БД..."
VIDEOS_COUNT=$(psql -h $DB_HOST -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM videos;" 2>/dev/null || echo "0")

if [ "$VIDEOS_COUNT" -eq "0" ]; then
    echo "База пустая - загружаем данные из JSON..."
    python loader.py /app/data.json
    echo "Данные загружены!"
else
    echo "В базе уже есть $VIDEOS_COUNT видео"
fi

# Запускаем тест БД
echo ""
echo "Тестирование подключения к БД..."
python test_db.py

# Запускаем бота
echo ""
echo "ЗАПУСК TELEGRAM БОТА"
python bot.py
