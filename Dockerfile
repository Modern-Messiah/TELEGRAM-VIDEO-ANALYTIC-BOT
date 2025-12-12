# Используем официальный Python образ
FROM python:3.11-slim

# Отключаем буферизацию stdout/stderr
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/entrypoint.sh

# Запускаем через entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
