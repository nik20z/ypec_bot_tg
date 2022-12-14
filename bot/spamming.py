from datetime import datetime, timedelta
import time
from loguru import logger

from aiogram import Dispatcher
from aiogram.utils.exceptions import BadRequest
from aiogram.utils.exceptions import BotBlocked
from aiogram.utils.exceptions import BotKicked
from aiogram.utils.exceptions import UserDeactivated
from aiogram.utils.exceptions import CantInitiateConversation
from aiogram.utils.exceptions import ChatNotFound

# My Modules
from bot.config import GOD_ID
from bot.config import AnswerText

from bot.database import Table
from bot.database import Insert
from bot.database import Update
from bot.database import Select
from bot.database import Delete

from bot.message_timetable import MessageTimetable

from bot.parse import TimetableHandler


def get_next_check_time(array_times: list, func_name: str):
    """Расчет времени до следующего цикла в зависимости от имени функции"""

    delta = 0
    one_second = 0

    now = datetime.now()
    week_day_id = now.weekday()
    type_week_day = "saturday" if week_day_id == 5 else "weekday"

    for t in array_times[func_name][type_week_day]:
        now = datetime.now()

        one_second = round(now.microsecond / 1000000)

        check_t = datetime.strptime(t, "%H:%M")

        delta = timedelta(hours=now.hour - check_t.hour,
                          minutes=now.minute - check_t.minute,
                          seconds=now.second - check_t.second)

        if week_day_id == 6:
            break

        seconds = delta.total_seconds()
        if seconds < 0:
            return seconds * (-1) + one_second

    seconds = (timedelta(hours=24) - delta).total_seconds()
    return seconds + one_second


async def check_replacement(dp: Dispatcher):
    """Функция для проверки наличия замен"""
    th = TimetableHandler()

    await dp.bot.send_message(chat_id=GOD_ID, text='Check Replacements')

    rep_result = await th.get_replacement(day="tomorrow")

    if rep_result != "NO":
        """Если замены отсутствуют, то чистим таблицы"""
        Delete.ready_timetable_by_date(th.date_replacement)

        th.get_ready_timetable(date_=th.date_replacement,
                               lesson_type=th.week_lesson_type)

        if rep_result == "NEW":
            Insert.time_replacement_appearance()
            await dp.bot.send_message(chat_id=GOD_ID, text='NEW')
            await start_spamming(dp, th.date_replacement, get_all_ids=True)

        elif rep_result == "UPDATE":
            await dp.bot.send_message(chat_id=GOD_ID, text='UPDATE')
            await start_spamming(dp, th.date_replacement)
    

    Table.delete('replacement_temp')
    Insert.replacement(th.rep.data, table_name="replacement_temp")


async def start_spamming(dp: Dispatcher, date_, get_all_ids=False):
    """Начало рассылки сообщений, если имеются id"""
    t_start = time.time()
    count_send_msg = 0
    count_pin_msg = 0
    names_array = []

    for table_name in ("group_", "teacher"):

        if get_all_ids:
            spam_ids = Select.all_info(table_name=table_name, column_name=f"{table_name}_id")
        else:
            spam_ids = Select.names_rep_different(table_name)

        for name_id in spam_ids:
            
            if name_id is None:
                continue

            name_ = Select.name_by_id(table_name, name_id)
            names_array.append(name_)

            spam_user_data = Select.user_ids_telegram_by(table_name, name_id)

            """Не делаем запрос, если нет id пользователей для рассылки"""
            data_ready_timetable = Select.ready_timetable(table_name, date_, name_)

            for user_data in spam_user_data:
                """Перебираем массивы с данными пользователей"""
                try:
                    [user_id, pin_msg, view_name, view_add, view_time] = user_data

                    text = MessageTimetable(name_,
                                            date_,
                                            data_ready_timetable,
                                            view_name=view_name,
                                            view_add=view_add,
                                            view_time=view_time).get()
                    try:
                        message = await dp.bot.send_message(user_id, text=text)
                        count_send_msg += 1
                        logger.info(f"{user_id} | {table_name} | {name_id} | {name_}")
                        
                        
                        if pin_msg:
                            """Если пользователь просит закрепить сообщение"""
                            try:
                                await dp.bot.pin_chat_message(user_id, message.message_id)
                                count_pin_msg += 1

                            except BadRequest:
                                if user_id < 0:
                                    await dp.bot.send_message(user_id, text=AnswerText.error["not_msg_pin"])
                                    Update.user_settings(user_id, 'pin_msg', 'False', convert_val_text=False)
                    
                    except (BotBlocked, BotKicked, UserDeactivated, ChatNotFound) as e:
                        logger.info(f"{e} {user_id}")
                        Update.user_settings(user_id, 'spamming', 'False', convert_val_text=False)
                        # Update.user_settings(user_id, 'bot_blocked', 'True', convert_val_text=False)

                    #await asyncio.sleep(.05)
                
                except Exception as e:
                    logger.info(f"{e} {user_id}")
                    await dp.bot.send_message(GOD_ID, text=text_except)

    time_spamming = round(time.time() - t_start, 2)

    stat_message = f"Отправлено: {count_send_msg}\n" \
                   f"Закреплено: {count_pin_msg}\n" \
                   f"Общее время рассылки: {time_spamming}\n" \
                   f"Изменилось расписание для: {', '.join(names_array)}"
    await dp.bot.send_message(GOD_ID, text=stat_message)
