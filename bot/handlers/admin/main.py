import sys
import time

from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.filters import IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import BotBlocked

# My modules
from bot.config import GOD_ID, ADMINS
from bot.config import ANSWER_TEXT
from bot.database import Insert
from bot.database import Delete
from bot.functions import get_rub_balance
# from bot.spamming import check_replacement
from bot.parse import TimetableHandler

from bot.misc import Qiwi


async def help_admin(message: Message):
    await message.answer(ANSWER_TEXT["help_admin"])


async def mailing_start(message: Message):
    """"""
    # ADMINS
    count = 0
    count_success = 0
    user_ids = open("bot/ypec_bot_old_users.txt")
    sending_message = message.get_args()

    for user_id in user_ids:
        count += 1
        try:
            #await message.bot.send_message(user_id, text=sending_message)
            count_success += 1
        except BotBlocked:
            pass

    text = f"Успешно: {count_success}\nНеудачно: {count - count_success}\nВсего user_ids: {count}"
    await message.bot.send_message(GOD_ID, text=text)


async def delete_user(message: Message):
    """Удаляем себя из таблицы telegram"""
    Delete.user(message.chat.id)


async def get_main_timetable(message: Message):
    """Парсим основное расписание"""
    t = time.time()
    TimetableHandler().get_main_timetable(type_name='group_', names=[])

    await message.answer(f"Основное расписание получено за {round(time.time() - t)}")


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

    await message.answer(f"Баланс Qiwi-кошелька обновлён: {rub_balance} ₽")


async def update_timetable(message: Message):
    """Проверяем замены и составляем готовое расписание"""
    # await check_replacement(dp)
    pass


async def restart_bot(message: Message):
    """Перезапускаем бота"""
    await message.answer("restart_bot")
    sys.exit()


async def info_log(message: Message):
    user_id = message.chat.id
    await message.bot.send_document(user_id, open("bot/log/info.log"))


'''
async def error_log(message: Message):
    user_id = message.chat.id
    await message.bot.send_document(user_id, open("bot/log/error.log"))
'''


def register_admin_handlers(dp: Dispatcher):
    # todo: register all admin handlers

    dp.register_message_handler(help_admin,
                                IDFilter(chat_id=ADMINS),
                                commands=['help_admin'])

    dp.register_message_handler(mailing_start,
                                IDFilter(chat_id=ADMINS),
                                commands=['mailing'])

    dp.register_message_handler(delete_user,
                                IDFilter(chat_id=ADMINS),
                                commands=['delete_user'])

    dp.register_message_handler(get_main_timetable,
                                IDFilter(chat_id=ADMINS),
                                commands=['get_main_timetable'])

    dp.register_message_handler(get_replacement,
                                IDFilter(chat_id=ADMINS),
                                commands=['get_replacement'])

    dp.register_message_handler(update_balance,
                                IDFilter(chat_id=ADMINS),
                                commands=['update_balance'])

    dp.register_message_handler(update_timetable,
                                IDFilter(chat_id=ADMINS),
                                commands=['update_timetable'])

    dp.register_message_handler(restart_bot,
                                IDFilter(chat_id=ADMINS),
                                commands=['restart_bot'])

    dp.register_message_handler(info_log,
                                IDFilter(chat_id=ADMINS),
                                commands=['info_log'])

    '''
    .register_message_handler(error_log,
                                IDFilter(chat_id=ADMINS),
                                commands=['error_log'])
    '''

