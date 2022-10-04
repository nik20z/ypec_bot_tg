import asyncio
from aiogram import Bot, Dispatcher

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from aiogram.dispatcher import DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.middlewares import BaseMiddleware

from aiogram.types import Message, BotCommand

from aiogram.utils import executor
from aiogram.utils.exceptions import Throttled

from bot.config import array_times

from bot.database import Table

from bot.filters import register_all_filters
from bot.functions import get_next_check_time
from bot.handlers import register_all_handlers

from bot.misc import TgKeys

from bot.spamming import check_replacement

from bot.config import WEBHOOK_URL
from bot.config import WEBHOOK_PATH
from bot.config import WEBAPP_HOST
from bot.config import WEBAPP_PORT


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: Message, data: dict):

        # Get current handler
        handler = current_handler.get()

        # Get dispatcher from context
        dispatcher = Dispatcher.get_current()
        # If handler was configured, get rate limit and key from handler
        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        # Use Dispatcher.throttle method.
        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            # Execute action
            await self.message_throttled(message, t)

            # Cancel current handler
            raise CancelHandler()

    async def message_throttled(self, message: Message, throttled: Throttled):

        handler = current_handler.get()
        dispatcher = Dispatcher.get_current()
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        # Calculate how many time is left till the block ends
        delta = throttled.rate - throttled.delta

        # Prevent flooding
        if throttled.exceeded_count <= 2:
            await message.reply('Перестань спамить!')

        # Sleep.
        await asyncio.sleep(delta)

        '''
        # Check lock status
        thr = await dispatcher.check_key(key)

        # If current message is not last with current key - do not send message
        if thr.exceeded_count == throttled.exceeded_count:
            await message.reply('Unlocked.')
        '''


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
        BotCommand("help", "Помощь")
    ])


async def on_startup(dp: Dispatcher) -> None:
    # await dp.bot.set_webhook(WEBHOOK_URL)
    register_all_filters(dp)
    register_all_handlers(dp)


async def on_shutdown(dp: Dispatcher) -> None:
    # await dp.bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


def start_bot():
    Table.create()
    Table.create_view()

    bot = Bot(token=TgKeys.TOKEN, parse_mode='HTML')
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
