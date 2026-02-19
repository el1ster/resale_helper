import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from bot.handlers import router
from database import init_db

# Завантаження змінних оточення
load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Перевірка та ініціалізація БД при старті
    init_db()
    
    # Отримання токена Telegram-бота
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("Помилка: BOT_TOKEN не знайдено у файлі .env!")
        return

    # Ініціалізація бота та диспетчера
    bot = Bot(token=token)
    dp = Dispatcher()
    
    # Реєстрація роутерів
    dp.include_router(router)
    
    logger.info("Бот EVS успішно запущений та готовий до роботи.")
    
    # Запуск polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинено.")
