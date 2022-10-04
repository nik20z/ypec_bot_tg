from aiogram import Dispatcher
from aiogram.utils.exceptions import BadRequest

from bot.config import GOD_ID
from bot.config import ANSWER_TEXT

from bot.database import Table
from bot.database import Insert
from bot.database import Update
from bot.database import Select
from bot.database import Delete

from bot.functions import get_message_timetable
from bot.functions import get_day_text

from bot.parse import TimetableHandler


async def check_replacement(dp: Dispatcher):
    """Функция для проверки наличия замен"""
    th = TimetableHandler()

    await dp.bot.send_message(chat_id=GOD_ID, text='Check Replacements')

    rep_result = th.get_replacement(day="tomorrow")

    if rep_result != "NO":

        Delete.ready_timetable_by_date(th.date_replacement)

        th.get_ready_timetable(date_=th.date_replacement,
                               lesson_type=th.week_lesson_type)

        if rep_result == "NEW":
            await start_spamming(dp, get_all_ids=True)

        elif rep_result == "UPDATE":
            await start_spamming(dp)

    # после прохождения цикла обновляем данные замен во временной таблице
    Table.delete('replacement_temp')
    Insert.replacement(th.rep.data, table_name="replacement_temp")


async def start_spamming(dp: Dispatcher, get_all_ids=False):
    """Начало рассылки сообщений, если имеются id"""
    date_ = get_day_text(days=1)

    for table_name in ("group_", "teacher"):

        if get_all_ids:
            spam_ids = Select.all_info(table_name=table_name, colomn_name=f"{table_name}_id")
        else:
            spam_ids = Select.names_rep_different(table_name)

        for name_id in spam_ids:

            name_ = Select.value_by_id(table_name_=table_name,
                                       colomn_names=[f"{table_name}_name"],
                                       id_=name_id,
                                       check_id_name_colomn=f"{table_name}_id")

            spam_user_data = Select.user_ids_telegram_by(table_name, name_id)

            for user_data in spam_user_data:

                [user_id, pin_msg, view_name, view_add, view_time] = user_data

                data_ready_timetable = Select.ready_timetable(table_name, date_, name_)

                text = get_message_timetable(name_,
                                             date_,
                                             data_ready_timetable,
                                             view_name=view_name,
                                             view_add=view_add,
                                             view_time=view_time)

                message = await dp.bot.send_message(user_id, text=text)

                if pin_msg:
                    try:
                        await dp.bot.pin_chat_message(user_id, message.message_id)
                    except BadRequest:
                        if user_id < 0:
                            await dp.bot.send_message(user_id, text=ANSWER_TEXT["error"]["not_msg_pin"])
                            Update.user_settings(user_id, 'pin_msg', 'False', convert_val_text=False)
