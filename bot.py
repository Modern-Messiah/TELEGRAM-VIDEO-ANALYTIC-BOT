import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

from llm_handler import process_natural_language_query

load_dotenv()

# Инициализация бота
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    welcome_text = """
👋 Привет! Я бот для аналитики видео.

Задавай мне вопросы на русском языке, например:
• Сколько всего видео?
• Сколько видео набрало больше 100000 просмотров?
• На сколько просмотров выросли все видео 28 ноября 2025?
• Сколько видео у креатора с id ... ?

Я отвечу одним числом! 📊
    """
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработка команды /help"""
    help_text = """
📚 Примеры вопросов:

1️⃣ Общая статистика:
   • Сколько всего видео есть в системе?
   • Сколько видео набрало больше 100000 просмотров?

2️⃣ По креаторам:
   • Сколько видео у креатора с id XXX?
   • Сколько видео у креатора XXX вышло с 1 по 5 ноября 2025?

3️⃣ Динамика:
   • На сколько просмотров выросли все видео 28 ноября 2025?
   • Сколько видео получали новые просмотры 27 ноября 2025?

Просто напиши свой вопрос! 🚀
    """
    await message.answer(help_text)


@dp.message()
async def handle_question(message: types.Message):
    """Обработка вопросов пользователя"""
    user_question = message.text or ""
    username = message.from_user.username if message.from_user else "unknown"
    print(
        f"\n📩 Получен вопрос от @{username}: {user_question}",
        flush=True,
    )

    try:
        # Обрабатываем вопрос через LLM
        result = await process_natural_language_query(user_question)

        # Отправляем результат
        await message.answer(str(result))
        print(f"Ответ отправлен: {result}", flush=True)

    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        print(error_msg, flush=True)
        await message.answer(
            "Не удалось обработать запрос. Попробуйте переформулировать вопрос."
        )


async def main():
    # Главная функция запуска бота
    import sys

    print("Бот запущен и готов к работе!", flush=True)
    bot_info = await bot.get_me()
    print(f"Bot username: @{bot_info.username}", flush=True)
    sys.stdout.flush()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
