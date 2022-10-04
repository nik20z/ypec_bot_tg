from io import StringIO
import time

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.filters import IDFilter

from bot.database import Insert, Delete
from bot.parse import TimetableHandler
from bot.functions import get_rub_balance

from bot.misc import Qiwi


async def delete_user(message: Message):
    """Удаляем себя из таблицы telegram"""
    Delete.user(message.chat.id)


async def get_main_timetable(message: Message):
    """Парсим основное расписание"""
    t = time.time()
    TimetableHandler().get_main_timetable(type_name='group_', names=[])

    await message.answer(f"Основное расписание получено за {time.time() - t}")


async def get_replacement(message: Message):
    """Получаем замены"""
    th = TimetableHandler()
    th.get_replacement(day="tomorrow")

    if th.rep.data:
        return await message.answer(f"Замены на {th.date_replacement} получены")

    await message.answer(f"Замен нет")


async def update_balance(message: Message):
    """Обновляем данные о балансе Qiwi-кошелька"""
    rub_balance = get_rub_balance(Qiwi.NUMBER_PHONE, Qiwi.TOKEN)
    Insert.config('rub_balance', rub_balance)

    await message.answer(f"Баланс Qiwi-кошелька обновлён: {rub_balance}")


async def update_timetable(message: Message):
    """Проверяем замены и составляем готовое расписание"""
    pass


async def send_document(message: Message):
    text = """some text ..."""
    file = StringIO(text)
    await bot.send_document(file)


def register_admin_handlers(dp: Dispatcher):
    # todo: register all admin handlers

    global bot
    bot = dp.bot

    dp.register_message_handler(delete_user,
                                IDFilter(chat_id=[1020624735]),
                                commands=['delete_user'])

    dp.register_message_handler(get_main_timetable,
                                IDFilter(chat_id=[1020624735]),
                                commands=['get_main_timetable'])

    dp.register_message_handler(get_replacement,
                                IDFilter(chat_id=[1020624735]),
                                commands=['get_replacement'])

    dp.register_message_handler(update_balance,
                                IDFilter(chat_id=[1020624735]),
                                commands=['update_balance'])

    dp.register_message_handler(update_timetable,
                                IDFilter(chat_id=[1020624735]),
                                commands=['update_timetable'])

    dp.register_message_handler(send_document,
                                IDFilter(chat_id=[1020624735]),
                                commands=['send_document'])
