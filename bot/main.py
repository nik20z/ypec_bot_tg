import asyncio

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from aiogram.utils import executor
import nest_asyncio

# My Modules
from bot.config import array_times
from bot.database import Table
from bot.filters import register_all_filters
from bot.handlers import register_all_handlers
from bot.misc import Keys
from bot.spamming import check_replacement
from bot.spamming import get_next_check_time
from bot.throttling import ThrottlingMiddleware


def repeat(func, dp, loop_repeat):
    """Функция-повторитель для loop"""
    asyncio.ensure_future(func(dp), loop=loop_repeat)
    interval = get_next_check_time(array_times, func.__name__)
    loop_repeat.call_later(interval, repeat, func, dp, loop_repeat)


async def set_default_commands(dp: Dispatcher) -> None:
    await dp.bot.set_my_commands([
        BotCommand("start", "Запуск бота"),
        BotCommand("timetable", "Расписание"),
        BotCommand("settings", "Настройки"),
        BotCommand("help", "Помощь"),
        BotCommand("call_schedule", "Расписание звонков"),
        BotCommand("show_keyboard", "Показать клавиатуру")
    ])


async def on_startup(dp: Dispatcher) -> None:
    # await dp.bot.set_webhook(WEBHOOK_URL)
    register_all_filters(dp)
    register_all_handlers(dp)


async def on_shutdown(dp: Dispatcher) -> None:
    # await dp.bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


def start_telegram_bot():
    nest_asyncio.apply()

    Table.create()
    Table.create_view()

    bot = Bot(token=Keys.TG_TOKEN, parse_mode='HTML')
    dp = Dispatcher(bot, storage=MemoryStorage())

    dp.middleware.setup(LoggingMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(set_default_commands(dp))]
    loop.run_until_complete(asyncio.wait(tasks))

    loop.call_later(1, repeat, check_replacement, dp, loop)

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

    '''
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )'''
