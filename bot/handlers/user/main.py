import asyncio
from aiogram import Dispatcher
# from aiogram import types
from aiogram.types import Message, CallbackQuery

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

# from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, BotBlocked
# from aiogram.utils.exceptions import MessageTextIsEmpty

import aiogram.utils.markdown as fmt

from datetime import datetime
from io import StringIO
from loguru import logger
import random

from bot.database import Select
from bot.database import Insert
from bot.database import Update

from bot.config import AnswerText
from bot.config import AnswerCallback
from bot.config import ADMINS

from bot.keyboards import Inline
from bot.keyboards import Reply

from bot.message_timetable import MessageTimetable

from bot.handlers.functions import check_call
from bot.handlers.functions import get_callback_values
from bot.handlers.functions import column_name_by_callback
from bot.functions import get_week_day_name_by_id
from bot.functions import month_translate

from bot.throttling import rate_limit


class UserStates(StatesGroup):
    """Класс состояний пользователя"""
    choise_type_name = State()
    choise_name = State()


async def new_user(message: Message, state: FSMContext):
    """Обработчик для нового пользователя"""
    user_id = message.chat.id
    joined = message.date

    if user_id > 0:
        user_name = message.chat.first_name
        user_name_quote = fmt.quote_html(user_name)
        text = AnswerText.new_user["welcome_message_private"](user_name_quote)
    else:
        user_name = message.chat.title
        user_name_quote = fmt.quote_html(user_name)
        text = AnswerText.new_user["welcome_message_group"](user_name_quote)

    new_user_data = (user_id, user_name, joined)
    Insert.new_user(new_user_data)

    await state.update_data(send_help_message=True)
    await choise_type_name(message, text=text)

    logger.info(f"message {user_id} {user_name}")


async def choise_group__name(callback: CallbackQuery, course=1):
    """Выбор группы из списка для нового пользователя"""
    user_id = callback.message.chat.id

    Update.user_settings(user_id, "type_name", "True")
    group__names_array = Select.group_()

    text = AnswerText.new_user["choise_name"]("group_")
    keyboard = Inline.groups__list(group__names_array, course=course)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    await UserStates.choise_name.set()
    logger.info(f"callback {user_id}")


async def paging_group__list_state(callback: CallbackQuery):
    """Обработчик листания списка групп для новых пользователей"""
    await paging_group__list(callback, add_back_button=False)


async def paging_group__list(callback: CallbackQuery, last_ind=-2, add_back_button=True):
    """Обработчик листания списка групп"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]
    course = int(callback.data.split()[-1])

    group__names_array = Select.group_()

    text = AnswerText.new_user["choise_name"]("group_")
    keyboard = Inline.groups__list(group__names_array,
                                   course=course,
                                   add_back_button=add_back_button,
                                   last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {course}")


async def choise_teacher_name(callback: CallbackQuery):
    """Выбор преподавателя из списка для нового пользователя"""
    user_id = callback.message.chat.id

    Update.user_settings(user_id, "type_name", "False")
    teacher_names_array = Select.teacher()

    text = AnswerText.new_user["choise_name"]("teacher")
    keyboard = Inline.teachers_list(teacher_names_array)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    await UserStates.choise_name.set()
    logger.info(f"callback {user_id}")


async def paging_teacher_list_state(callback: CallbackQuery):
    """Обработчик листания списка преподавателей для новых пользователей"""
    await paging_teacher_list(callback, add_back_button=False)


async def paging_teacher_list(callback: CallbackQuery, last_ind=-2, add_back_button=True):
    """Обработчик листания списка преподавателей"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]
    start_ = int(callback.data.split()[-1])

    teacher_names_array = Select.teacher()

    text = AnswerText.new_user["choise_name"]("teacher")
    keyboard = Inline.teachers_list(teacher_names_array,
                                    start_=start_,
                                    add_back_button=add_back_button,
                                    last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {start_}")


@rate_limit(1)
async def error_choise_type_name_message(message: Message):
    """Обработчик левых сообщений при выборе профиля"""
    user_id = message.chat.id
    await message.answer(AnswerText.error["choise_type_name"])
    logger.info(f"message {user_id}")


async def choise_group_(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора группы для нового пользователя"""
    user_id = callback.message.chat.id
    type_name = "group_"
    group__id = callback.data.split()[-1]
    group__name = Select.name_by_id(type_name, group__id)

    Update.user_settings(user_id, "name_id", group__id)
    Update.user_settings_array(user_id, name_=type_name, value=group__id, remove_=None)
    Update.user_settings_array(user_id, name_="spam_group_", value=group__id, remove_=None)

    date_ = Select.fresh_ready_timetable_date(type_name=type_name, name_id=group__id)
    data_ready_timetable = Select.ready_timetable(type_name, date_, group__name)

    text = MessageTimetable(group__name,
                            date_,
                            data_ready_timetable).get()

    keyboard = Reply.default()

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerCallback.new_user["choise_group__name_finish"](group__name),
                                             show_alert=False)

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
    user_state_data = await state.get_data()
    await state.finish()

    logger.info(f"callback {user_id} {group__name} {group__id}")

    if "send_help_message" in user_state_data:
        await asyncio.sleep(2)
        await help_message(callback.message)


async def choise_teacher(callback: CallbackQuery, state: FSMContext):
    """Выбор преподавателя для нового пользователя"""
    user_id = callback.message.chat.id
    type_name = "teacher"
    teacher_id = callback.data.split()[-1]
    teacher_name = Select.name_by_id(type_name, teacher_id)

    Update.user_settings(user_id, "name_id", teacher_id)
    Update.user_settings_array(user_id, name_=type_name, value=teacher_id, remove_=None)
    Update.user_settings_array(user_id, name_="spam_teacher", value=teacher_id, remove_=None)

    date_ = Select.fresh_ready_timetable_date(type_name=type_name, name_id=teacher_id)
    data_ready_timetable = Select.ready_timetable(type_name, date_, teacher_name)

    text = MessageTimetable(teacher_name,
                            date_,
                            data_ready_timetable).get()
    keyboard = Reply.default()

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerCallback.new_user["choise_teacher_name_finish"](
                                                 teacher_name),
                                             show_alert=False)

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
    user_state_data = await state.get_data()
    await state.finish()

    logger.info(f"callback {user_id} {teacher_name} {teacher_id}")

    if "send_help_message" in user_state_data:
        await asyncio.sleep(2)
        await help_message(callback.message)


@rate_limit(1)
async def error_choise_name_message(message: Message):
    """Обработчик левых сообщений при выборе группы/преподавателя"""
    user_id = message.chat.id
    await message.answer(AnswerText.error["choise_name"])
    logger.info(f"message {user_id}")


async def choise_type_name(message: Message, text=None):
    """Выбор типа профиля"""
    user_id = message.chat.id

    if text is None:
        text = AnswerText.new_user["choise_type_name"]
    keyboard = Inline.type_names()

    await message.answer(text, reply_markup=keyboard)
    await UserStates.choise_type_name.set()
    logger.info(f"message {user_id}")


@rate_limit(1)
async def timetable(message: Message):
    """Обработчик запроса на получение Расписания"""
    user_id = message.chat.id

    user_info = Select.user_info_by_column_names(user_id)

    type_name = user_info[0]
    name_id = user_info[1]
    view_name = user_info[2]
    view_add = user_info[3]
    view_time = user_info[4]

    if type_name is None or name_id is None:
        """У пользователя нет основной подписки"""
        logger.info(f"message {user_id} {None} {name_id}")
        return await message.answer(AnswerText.no_main_subscription)

    name_ = Select.name_by_id(type_name, name_id)

    date_ = Select.fresh_ready_timetable_date(type_name=type_name, name_id=name_id)

    data_ready_timetable = Select.ready_timetable(type_name, date_, name_)

    text = MessageTimetable(name_,
                            date_,
                            data_ready_timetable,
                            view_name=view_name,
                            view_add=view_add,
                            view_time=view_time).get()
    keyboard = Reply.default()

    await message.answer(text, reply_markup=keyboard)
    logger.info(f"message {user_id} {name_} {name_id}")


@rate_limit(1)
async def command_timetable(message: Message):
    """Обработчик команды / timetable"""
    await timetable(message)


@rate_limit(1)
async def settings(message: Message, callback=None, edit_text=False):
    """Обработчик запроса на получение Настроек пользователя"""
    user_id = message.chat.id
    user_settings_data = list(Select.user_info(user_id))
    table_name = user_settings_data[0]
    name_id = user_settings_data[2]

    if name_id is not None:
        name_ = Select.name_by_id(table_name, name_id)
        user_settings_data[1] = name_

    text = AnswerText.settings
    keyboard = Inline.user_settings(user_settings_data)

    if edit_text:
        if callback is not None:
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.bot.answer_callback_query(callback.id)
    else:
        await message.answer(text, reply_markup=keyboard)

    logger.info(f"message {user_id}")


@rate_limit(1)
async def command_settings(message: Message):
    """Обработчик команды /settings"""
    await settings(message)


async def settings_callback(callback: CallbackQuery):
    """Обработчик CallbackQuery на возвращение к меню Настроек"""
    await settings(callback.message, callback, edit_text=True)


async def main_settings(callback: CallbackQuery):
    """Обработчик CallbackQuery на переход к окну основных настроек"""
    user_id = callback.message.chat.id
    user_settings_data = list(Select.user_info(user_id))

    text = AnswerText.main_settings
    keyboard = Inline.main_settings(user_settings_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def settings_info(callback: CallbackQuery):
    """Обработчик CallbackQuery для получения информации при нажатии кнопки"""
    user_id = callback.message.chat.id
    settings_name = callback.data.split()[-1]
    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerCallback.settings_info[settings_name],
                                             show_alert=True)
    logger.info(f"callback {user_id} {settings_name}")


async def update_main_settings_bool(callback: CallbackQuery):
    """Обновление настроек True/False"""
    user_id = callback.message.chat.id
    settings_name = callback.data.split()[-1]

    result = Update.user_settings_bool(user_id, name_=settings_name)

    await main_settings(callback)
    logger.info(f"callback {user_id} {settings_name} {result}")


async def support(callback: CallbackQuery, last_ind=-1):
    """Обработка нажатия кнопки support"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    rub_balance_value = 123     # Select.config("rub_balance")

    text = AnswerText.support
    keyboard = Inline.support(callback.data, last_callback_data, rub_balance_value)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def donate(callback: CallbackQuery, last_ind=-1):
    """Вывести меню с вариантами донейшинов"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    text = AnswerText.donate
    keyboard = Inline.donate(last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def future_updates(callback: CallbackQuery, last_ind=-1):
    """Вывести сообщение о будущих апдейтах"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    text = Select.config("future_updates")

    '''    
    if text in (None, ''):
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.error["default"])
    '''

    keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def spam_or_subscribe_name_id(callback: CallbackQuery, last_ind=-1):
    """Обновление настроек spamming и subscribe для карточек группы/преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, callback.data] = get_callback_values(callback, last_ind)

    type_column_name = callback_data_split[-1]
    action_type = type_column_name.split('_')[0]
    short_type_name = type_column_name.split('_')[-1]
    name_id = callback_data_split[-2]

    result = Update.user_settings_array(user_id,
                                        name_=column_name_by_callback.get(type_column_name),
                                        value=name_id)

    # удалили подписку
    if type_column_name in ('sub_gr', 'sub_tch') and not result:

        # если это карточка с активной основной подпиской, то удаляем её
        if Update.user_settings_value(user_id, "name_id", name_id, remove_=True):
            Update.user_settings(user_id, "type_name", "NULL", convert_val_text=False)

        Update.user_settings_array(user_id,
                                   name_=column_name_by_callback.get(f"sp_{short_type_name}"),
                                   value=name_id,
                                   remove_=True)

    elif type_column_name in ("sp_gr", "sp_tch") and result:

        Update.user_settings_array(user_id,
                                   name_=column_name_by_callback.get(f"sub_{short_type_name}"),
                                   value=name_id,
                                   remove_=None)

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerCallback.spam_or_subscribe_name_id(action_type, result),
                                             show_alert=False)

    logger.info(f"callback {user_id} {short_type_name} {action_type} {name_id} {result}")

    if short_type_name == "gr":
        await group__card(callback)

    elif short_type_name == "tch":
        await teacher_card(callback)


async def main_subscribe_name_id(callback: CallbackQuery, last_ind=-1):
    """Обновление настроек main_subscribe для карточек группы/преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, callback.data] = get_callback_values(callback, last_ind)
    type_column_name = callback_data_split[-1]
    name_id = callback_data_split[-2]

    result = Update.user_settings_value(user_id, "name_id", name_id)

    # если основная подписка добавлена
    if result:
        Update.user_settings(user_id, "type_name", type_column_name == "m_sub_gr", convert_val_text=True)
        Update.user_settings_array(user_id,
                                   name_=column_name_by_callback.get(type_column_name),
                                   value=name_id,
                                   remove_=None)
    else:
        Update.user_settings(user_id, "type_name", "NULL", convert_val_text=False)
        Update.user_settings(user_id, "name_id", "NULL", convert_val_text=False)

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerCallback.main_subscribe_name_id(result),
                                             show_alert=False)

    logger.info(f"{user_id} {type_column_name} {name_id} {result}")

    if type_column_name == 'm_sub_gr':
        await group__card(callback)

    elif type_column_name == 'm_sub_tch':
        await teacher_card(callback)


async def group__card(callback: CallbackQuery, last_ind=-2):
    """Показать карточку группы"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    group__id = callback_data_split[-1]

    group__user_info = Select.user_info_name_card("group_", user_id, group__id)
    group__name = group__user_info[1]

    text = AnswerText.group__card
    keyboard = Inline.group__card(group__user_info,
                                  callback_data=callback.data,
                                  last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {group__name} {group__id}")


async def teacher_card(callback: CallbackQuery, last_ind=-2):
    """Показать карточку преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    teacher_id = callback_data_split[-1]

    teacher_user_info = Select.user_info_name_card("teacher", user_id, teacher_id)
    teacher_name = teacher_user_info[1]

    text = AnswerText.teacher_card
    keyboard = Inline.teacher_card(teacher_user_info,
                                   callback_data=callback.data,
                                   last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {teacher_name} {teacher_id}")


async def lessons_list_by_teacher(callback: CallbackQuery, last_ind=-2):
    """Вывести список дисциплин, которые ведёт преподаватель"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    teacher_id = callback_data_split[-1]
    teacher_name = Select.name_by_id("teacher", teacher_id)

    lessons_list = Select.lessons_list_by_teacher(teacher_name)

    if not lessons_list:
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.not_lessons_list)

    text = f"<b>{teacher_name}</b>" \
           f"\n" \
           f"Список дисциплин:\n"
    for lesson_name in lessons_list:
        text += f" 🔹{lesson_name}\n"
    keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {teacher_name} {teacher_id}")


async def week_days_main_timetable(callback: CallbackQuery, last_ind=-1):
    """Показать список дней недели дня получения основного расписания"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    text = AnswerText.week_days_main_timetable
    keyboard = Inline.week_days_main_timetable(current_week_day_id=datetime.now().weekday(),
                                               callback_data=callback.data,
                                               last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def download_main_timetable(callback: CallbackQuery):
    """Скачать Основное расписание на неделю"""
    user_id = callback.message.chat.id
    callback_data_split = callback.data.split()

    type_name = column_name_by_callback.get(callback_data_split[-4])
    name_id = callback_data_split[-3]
    name_ = Select.name_by_id(type_name, name_id)

    text = f"{name_}\n\n"

    for week_day_id in range(6):
        week_day_name = get_week_day_name_by_id(week_day_id, bold=False)
        data_main_timetable = Select.view_main_timetable(type_name,
                                                         name_,
                                                         week_day_id=week_day_id,
                                                         lesson_type=None)
        main_timetable_message = MessageTimetable(name_,
                                                  week_day_name,
                                                  data_main_timetable,
                                                  start_text="",
                                                  view_name=False,
                                                  type_format="txt",
                                                  format_timetable="only_date").get()
        text += f"{main_timetable_message}\n\n"

    file = StringIO(text)
    file.name = f"{name_} На неделю {callback.id[-4:]}.txt"

    await callback.bot.send_chat_action(user_id, 'upload_document')
    await asyncio.sleep(2)
    await callback.bot.send_document(user_id, file)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {type_name} {name_} {name_id}")


async def get_main_timetable_by_week_day_id(callback: CallbackQuery, last_ind=-1):
    """Получить основное расписание для дня недели"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)

    week_day_id = callback_data_split[-1]

    type_name = column_name_by_callback.get(callback_data_split[-4])
    name_id = callback_data_split[-3]
    name_ = Select.name_by_id(type_name, name_id)

    data_main_timetable = Select.view_main_timetable(type_name, name_, week_day_id=week_day_id, lesson_type=None)

    if not data_main_timetable:
        week_day = get_week_day_name_by_id(week_day_id, type_case="prepositional", bold=False)
        text = AnswerCallback.not_timetable_by_week_day(week_day)
        await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                 text=text)

    else:
        date_week_day = get_week_day_name_by_id(week_day_id, type_case='prepositional')
        text = MessageTimetable(name_,
                                date_week_day,
                                data_main_timetable,
                                start_text="Основное расписание на ",
                                format_=True).get()
        keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.bot.answer_callback_query(callback.id)

    logger.info(f"callback {user_id} {type_name} {name_} {week_day_id} {bool(data_main_timetable)}")


async def months_history_ready_timetable(callback: CallbackQuery, last_ind=-1):
    """Вывести список с месяцами"""
    user_id = callback.message.chat.id
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    months_array = Select.months_ready_timetable()

    text = AnswerText.months_history_ready_timetable
    keyboard = Inline.months_ready_timetable(months_array, callback.data, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id}")


async def dates_ready_timetable(callback: CallbackQuery, last_ind=-1):
    """Вывести список дат"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    type_name = column_name_by_callback.get(callback_data_split[-4])
    name_id = callback_data_split[-3]
    month = callback_data_split[-1]

    name_ = Select.name_by_id(type_name, name_id)

    dates_array = Select.dates_ready_timetable(month=month,
                                               type_name=type_name,
                                               name_id=name_id)
    if not dates_array:
        """Если нет расписания ни на одну дату"""
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.not_ready_timetable_by_month(
                                                            month_translate(month)),
                                                        show_alert=False)

    text = AnswerText.dates_ready_timetable(name_, month_translate(month))
    keyboard = Inline.dates_ready_timetable(dates_array, callback.data, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {type_name} {name_} {name_id}")


async def download_ready_timetable_by_month(callback: CallbackQuery):
    """Скачать всё расписание на определённый месяц"""
    user_id = callback.message.chat.id
    callback_data_split = callback.data.split()

    type_name = column_name_by_callback.get(callback_data_split[-5])
    name_id = callback_data_split[-4]
    month = callback_data_split[-2]
    month_translate_text = month_translate(month)

    name_ = Select.name_by_id(type_name, name_id)

    text = f"{name_} {month_translate_text}\n\n"

    user_info = Select.user_info_by_column_names(user_id, column_names=['view_add', 'view_time'])
    view_add = user_info[0]
    view_time = user_info[1]

    dates_array = Select.dates_ready_timetable(month=month,
                                               type_name=type_name,
                                               name_id=name_id,
                                               type_sort='ASC')

    for date_ in dates_array:
        data_ready_timetable = Select.ready_timetable(type_name, date_, name_)
        date_text = date_.strftime('%d.%m.%Y')

        if data_ready_timetable:
            ready_timetable_message = MessageTimetable(name_,
                                                       date_text,
                                                       data_ready_timetable,
                                                       view_name=False,
                                                       view_add=view_add,
                                                       view_time=view_time).get()
            text += f"{ready_timetable_message}\n\n"

    file = StringIO(text)
    file.name = f"{name_} {month_translate(month)} {callback.id[-4:]}.txt"

    await callback.bot.send_chat_action(user_id, 'upload_document')
    await asyncio.sleep(2)
    await callback.bot.send_document(user_id, file)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {month} {type_name} {name_} {name_id}")


async def ready_timetable_by_date(callback: CallbackQuery):
    """Вывести расписание для определённой даты"""
    user_id = callback.message.chat.id
    callback_data_split = callback.data.split()
    type_name = column_name_by_callback.get(callback_data_split[-5])
    name_id = callback_data_split[-4]
    date_ = callback_data_split[-1]

    await view_ready_timetable(callback,
                               last_ind=-1,
                               type_name=type_name,
                               name_id=name_id,
                               date_=date_)
    logger.info(f"callback {user_id} {date_} {type_name} {name_id} name_id")


async def view_ready_timetable(callback: CallbackQuery, last_ind=-1, type_name=None, name_id=None, date_=None):
    """Показать текущее расписание"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)

    if type_name is None:
        type_name = column_name_by_callback.get(callback_data_split[-1])

    if name_id is None:
        name_id = callback_data_split[-2]

    if date_ is None:
        date_ = Select.fresh_ready_timetable_date(type_name=type_name, name_id=name_id)

        if date_ is None:
            """Расписание полностью отсутствует"""
            return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                            text=AnswerCallback.not_ready_timetable,
                                                            show_alert=False)

    user_info = Select.user_info_by_column_names(user_id, column_names=['view_add', 'view_time'])
    view_add = user_info[0]
    view_time = user_info[1]

    name_ = Select.name_by_id(type_name, name_id)

    data_ready_timetable = Select.ready_timetable(type_name, date_, name_)

    text = MessageTimetable(name_,
                            date_,
                            data_ready_timetable,
                            view_add=view_add,
                            view_time=view_time,
                            format_=False).get()
    keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)
    logger.info(f"callback {user_id} {type_name} {name_} {name_id}")


async def view_callback(callback: CallbackQuery):
    """Обработчик нажатий на пустые кнопки"""
    user_id = callback.message.chat.id
    text = ' '.join(callback.data.split()[1:])

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=text,
                                             show_alert=True)
    logger.info(f"callback {user_id}")


async def close(callback: CallbackQuery):
    """Обработать запрос на удаление (закрытие) окна сообщения"""
    user_id = callback.message.chat.id
    await callback.message.delete()
    logger.info(f"callback {user_id}")


@rate_limit(1)
async def call_schedule(message: Message):
    """Расписание звонков"""
    user_id = message.chat.id
    await message.answer(AnswerText.call_schedule)
    logger.info(f"callback {user_id}")


@rate_limit(1)
async def help_message(message: Message):
    """Вывести help-сообщение"""
    user_id = message.chat.id
    await message.answer(AnswerText.help)
    logger.info(f"message {user_id}")


@rate_limit(1)
async def show_keyboard(message: Message):
    """Показать клавиатуру"""
    user_id = message.chat.id

    text = AnswerText.show_keyboard
    keyboard = Reply.default()
    if user_id in ADMINS:
        keyboard = Reply.default_admin()

    await message.answer(text=text, reply_markup=keyboard)
    logger.info(f"message {user_id}")


@rate_limit(1)
async def other_messages(message: Message):
    """Обработчик сторонних сообщений"""
    user_id = message.chat.id
    text = random.choice(AnswerText.other_messages)

    await message.answer(text=text)
    logger.info(f"message {user_id}")


'''
async def bot_blocked(update: types.Update, exception: BotBlocked):
    pass
'''

'''
async def terminated_by_other_get_updates(update: types.Update, exception: TerminatedByOtherGetUpdates):
    await bot.send_message(chat_id=1020624735, text="Запущено 2 экземпляра бота")
'''

'''
MessageTextIsEmpty
'''


def register_user_handlers(dp: Dispatcher):
    # todo: register all user handlers

    dp.register_message_handler(new_user,
                                lambda msg: Select.user_info(user_id=msg.chat.id) is None,
                                content_types=['text'])

    dp.register_callback_query_handler(choise_group__name,
                                       lambda call: check_call(call, ['g_list']),
                                       state=UserStates.choise_type_name)

    dp.register_callback_query_handler(paging_group__list_state,
                                       lambda call: check_call(call, ['g_list'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(paging_group__list,
                                       lambda call: check_call(call, ['g_list'], ind=-2),
                                       state='*')

    dp.register_callback_query_handler(choise_teacher_name,
                                       lambda call: check_call(call, ['t_list']),
                                       state=UserStates.choise_type_name)

    dp.register_callback_query_handler(paging_teacher_list_state,
                                       lambda call: check_call(call, ['t_list'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(paging_teacher_list,
                                       lambda call: check_call(call, ['t_list'], ind=-2),
                                       state='*')

    dp.register_message_handler(error_choise_type_name_message, state=UserStates.choise_type_name)

    # dp.register_message_handler(error_choise_type_name_callback, state=UserStates.choise_type_name)

    dp.register_callback_query_handler(choise_group_,
                                       lambda call: check_call(call, ['gc'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(choise_teacher,
                                       lambda call: check_call(call, ['tc'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_message_handler(error_choise_name_message, state=UserStates.choise_name)

    # dp.register_message_handler(error_choise_name_callback, state=UserStates.choise_name)

    dp.register_message_handler(choise_type_name,
                                commands=['start'],
                                state='*')

    dp.register_message_handler(timetable, Text(contains=['Расписание'], ignore_case=True))

    dp.register_message_handler(command_timetable, commands=['timetable'])

    dp.register_message_handler(settings, Text(contains=['Настройки'], ignore_case=True))

    dp.register_message_handler(command_settings, commands=['settings'])

    dp.register_callback_query_handler(settings_callback,
                                       lambda call: check_call(call, ['s']))

    dp.register_callback_query_handler(main_settings,
                                       lambda call: check_call(call, ['ms']))

    dp.register_callback_query_handler(settings_info,
                                       lambda call: check_call(call, ['settings_info'], ind=-2))

    dp.register_callback_query_handler(update_main_settings_bool,
                                       lambda call: check_call(call, ['update_main_settings_bool'], ind=-2))

    dp.register_callback_query_handler(support,
                                       lambda call: check_call(call, ['support']))

    dp.register_callback_query_handler(donate,
                                       lambda call: check_call(call, ['donate']))

    dp.register_callback_query_handler(future_updates,
                                       lambda call: check_call(call, ['future_updates']))

    dp.register_callback_query_handler(spam_or_subscribe_name_id,
                                       lambda call: check_call(call, ['sp_gr', 'sub_gr', 'sp_tch', 'sub_tch']))

    dp.register_callback_query_handler(main_subscribe_name_id,
                                       lambda call: check_call(call, ['m_sub_gr', 'm_sub_tch']))

    dp.register_callback_query_handler(group__card,
                                       lambda call: check_call(call, ['gc'], ind=-2))

    dp.register_callback_query_handler(teacher_card,
                                       lambda call: check_call(call, ['tc'], ind=-2))

    dp.register_callback_query_handler(lessons_list_by_teacher,
                                       lambda call: check_call(call, ['lessons_list'], ind=-2))

    dp.register_callback_query_handler(week_days_main_timetable,
                                       lambda call: check_call(call, ['wdmt']))

    dp.register_callback_query_handler(download_main_timetable,
                                       lambda call: check_call(call, ['download_main_timetable']))

    dp.register_callback_query_handler(get_main_timetable_by_week_day_id,
                                       lambda call: check_call(call, ['wdmt'], ind=-2))

    dp.register_callback_query_handler(months_history_ready_timetable,
                                       lambda call: check_call(call, ['mhrt']))

    dp.register_callback_query_handler(dates_ready_timetable,
                                       lambda call: check_call(call, ['mhrt'], ind=-2))

    dp.register_callback_query_handler(download_ready_timetable_by_month,
                                       lambda call: check_call(call, ['download_ready_timetable_by_month']))

    dp.register_callback_query_handler(ready_timetable_by_date,
                                       lambda call: check_call(call, ['mhrt'], ind=-3))

    dp.register_callback_query_handler(view_ready_timetable,
                                       lambda call: check_call(call, ['g_rt', 't_rt']))

    dp.register_callback_query_handler(view_callback,
                                       lambda call: call.data.split()[0] == '*')

    dp.register_callback_query_handler(close,
                                       lambda call: call.data == 'close', state='*')

    dp.register_message_handler(call_schedule,
                                commands=['call_schedule'],
                                state='*')

    dp.register_message_handler(help_message,
                                commands=['help'],
                                state='*')

    dp.register_message_handler(show_keyboard,
                                commands=['show_keyboard'],
                                state='*')

    dp.register_message_handler(other_messages,
                                state='*')

    # dp.register_errors_handler(terminated_by_other_get_updates, exception=TerminatedByOtherGetUpdates)
