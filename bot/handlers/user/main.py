import asyncio
from aiogram import Dispatcher
from aiogram import types
from aiogram.types import Message, CallbackQuery

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, BotBlocked

from io import StringIO

from bot.database import Select, Insert, Update

from bot.config import ANSWER_TEXT
from bot.config import ANSWER_CALLBACK

from bot.keyboards import Inline
from bot.keyboards import Reply

from bot.functions import get_message_timetable
from bot.functions import check_call
from bot.functions import get_callback_values
from bot.functions import colomn_name_by_callback
from bot.functions import get_day_text
from bot.functions import get_week_day_name_by_id
from bot.functions import month_translate

from bot.throttling import rate_limit


class UserStates(StatesGroup):
    """Класс состояний пользователя

    choise_type_name -- состояние выбора типа профиля (студент/преподаватель)
    choise_name -- выбор названия группы или преподавателя

    """
    choise_type_name = State()
    choise_name = State()


async def new_user(message: Message, state: FSMContext):
    """Обработчик для нового пользователя"""
    user_id = message.chat.id
    joined = message.date

    if user_id > 0:
        user_name = message.chat.first_name
        text = ANSWER_TEXT["new_user"]["welcome_message_private"](user_name)
    else:
        user_name = message.chat.title
        text = ANSWER_TEXT["new_user"]["welcome_message_group"](user_name)

    new_user_data = (user_id, user_name, joined)
    Insert.new_user(new_user_data)

    await state.update_data(send_help_message=True)
    await choise_type_name(message, text=text)


async def choise_type_name(message: Message, text=None):
    """Выбор типа профиля"""
    if text is None:
        text = ANSWER_TEXT["new_user"]["choise_type_name"]
    keyboard = Inline.type_names()

    await message.answer(text, reply_markup=keyboard)
    await UserStates.choise_type_name.set()


async def choise_group__name(callback: CallbackQuery, course=1):
    """Выбор группы из списка для нового пользователя"""
    user_id = callback.message.chat.id

    Update.user_settings(user_id, 'type_name', 'True')
    group__name_array = Select.group_()

    text = ANSWER_TEXT["new_user"]["choise_name"]('group_')
    keyboard = Inline.groups__list(group__name_array, course=course)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)
    await UserStates.choise_name.set()


async def paging_group__list_state(callback: CallbackQuery):
    """Обработчик листания списка групп для новых пользователей"""
    await paging_group__list(callback, add_back_button=False)


async def paging_group__list(callback: CallbackQuery, last_ind=-2, add_back_button=True):
    """Обработчик листания списка групп"""
    last_callback_data = ' '.join(callback.data.split()[:last_ind])
    course = int(callback.data.split()[-1])

    group__name_array = Select.group_()

    text = ANSWER_TEXT["new_user"]["choise_name"]('group_')
    keyboard = Inline.groups__list(group__name_array,
                                   course=course,
                                   add_back_button=add_back_button,
                                   last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def choise_teacher_name(callback: CallbackQuery):
    """Выбор преподавателя из списка для нового пользователя"""
    user_id = callback.message.chat.id

    Update.user_settings(user_id, 'type_name', 'False')
    teacher_name_array = Select.teacher()

    text = ANSWER_TEXT["new_user"]["choise_name"]('teacher')
    keyboard = Inline.teachers_list(teacher_name_array)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)
    await UserStates.choise_name.set()


async def paging_teacher_list_state(callback: CallbackQuery):
    """Обработчик листания списка преподавателей для новых пользователей"""
    await paging_teacher_list(callback, add_back_button=False)


async def paging_teacher_list(callback: CallbackQuery, last_ind=-2, add_back_button=True):
    """Обработчик листания списка преподавателей"""
    last_callback_data = ' '.join(callback.data.split()[:last_ind])
    start_ = int(callback.data.split()[-1])

    teacher_name_array = Select.teacher()

    text = ANSWER_TEXT["new_user"]["choise_name"]('teacher')
    keyboard = Inline.teachers_list(teacher_name_array,
                                    start_=start_,
                                    add_back_button=add_back_button,
                                    last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def error_choise_type_name(message: Message):
    """Обработчик левых сообщений от новых пользователей при выборе профиля"""
    await message.answer(ANSWER_TEXT["error"]["choise_type_name"])


async def choise_group_(callback: CallbackQuery, state: FSMContext):
    """Выбор группы для нового пользователя"""
    user_id = callback.message.chat.id
    group__id = callback.data.split()[-1]
    group__name = Select.name_by_id("group_", group__id)

    Update.user_settings(user_id, 'name_id', group__id)
    Update.user_settings_array(user_id, name_='group_', value=group__id)
    Update.user_settings_array(user_id, name_='spam_group_', value=group__id)

    date_ = get_day_text(days=1)
    data_ready_timetable = Select.ready_timetable("group_", date_, group__name)

    text = get_message_timetable(group__name, date_, data_ready_timetable)
    keyboard = Reply.default()

    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=ANSWER_CALLBACK['new_user']['choise_group__name_finish'](group__name),
                                    show_alert=False)

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)

    await state.finish()

    if 'send_help_message' in await state.get_data():
        await asyncio.sleep(2)
        await help_message(callback.message)


async def choise_teacher(callback: CallbackQuery, state: FSMContext):
    """Выбор преподавателя для нового пользователя"""
    user_id = callback.message.chat.id
    teacher_id = callback.data.split()[-1]
    teacher_name = Select.name_by_id("teacher", teacher_id)

    Update.user_settings(user_id, 'name_id', teacher_id)
    Update.user_settings_array(user_id, name_='teacher', value=teacher_id)
    Update.user_settings_array(user_id, name_='spam_teacher', value=teacher_id)

    date_ = get_day_text(days=1)
    data_ready_timetable = Select.ready_timetable("teacher", date_, teacher_name)

    text = get_message_timetable(teacher_name, date_, data_ready_timetable)
    keyboard = Reply.default()

    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=ANSWER_CALLBACK['new_user']['choise_teacher_name_finish'](teacher_name),
                                    show_alert=False)

    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)

    await state.finish()

    if 'send_help_message' in await state.get_data():
        await asyncio.sleep(2)
        await help_message(callback.message)


async def error_choise_name(message: Message):
    """Обработчик левых сообщений от новых пользователей при выборе группы/преподавателя"""
    await message.answer(ANSWER_TEXT["error"]["choise_name"])


@rate_limit(1)
async def timetable(message: Message):
    """Обработчик запроса на получение Расписания"""
    user_id = message.chat.id

    user_info = Select.user_info_by_colomn_names(user_id)

    type_name = user_info[0]
    name_id = user_info[1]
    view_name = user_info[2]
    view_add = user_info[3]
    view_time = user_info[4]

    if type_name is None:
        """У пользователя нет основной подписки"""
        return await message.answer(ANSWER_TEXT['no_main_subscription'])

    name_ = Select.name_by_id(type_name, name_id)

    date_ = get_day_text()
    if Select.check_filling_table("replacement"):
        """Если в таблице есть замены"""
        date_ = get_day_text(days=1)

    data_ready_timetable = Select.ready_timetable(type_name, date_, name_)

    text = get_message_timetable(name_,
                                 date_,
                                 data_ready_timetable,
                                 view_name=view_name,
                                 view_add=view_add,
                                 view_time=view_time)
    keyboard = Reply.default()

    await message.answer(text, reply_markup=keyboard)


async def command_timetable(message: Message):
    """Обработчик команды /timatable"""
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

    text = ANSWER_TEXT['settings']
    keyboard = Inline.user_settings(user_settings_data)

    if edit_text:
        if callback is not None:
            await callback.message.edit_text(text, reply_markup=keyboard)
            await bot.answer_callback_query(callback.id)
    else:
        await message.answer(text, reply_markup=keyboard)


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

    text = ANSWER_TEXT['main_settings']
    keyboard = Inline.main_settings(user_settings_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def settings_info(callback: CallbackQuery):
    """Обработчик CallbackQuery для получения информации при нажатии кнопки"""
    settings_name = callback.data.split()[-1]
    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=ANSWER_CALLBACK['settings_info'][settings_name],
                                    show_alert=True)


async def update_main_settings_bool(callback: CallbackQuery):
    """Обновление настроек True/False"""
    user_id = callback.message.chat.id
    settings_name = callback.data.split()[-1]

    Update.user_settings_bool(user_id, name_=settings_name)

    await main_settings(callback)


async def support(callback: CallbackQuery, last_ind=-1):
    """Обработка нажатия кнопки support """
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    rub_balance_value = Select.config('rub_balance')

    text = ANSWER_TEXT['support']
    keyboard = Inline.support(callback.data, last_callback_data, rub_balance_value)

    await callback.message.edit_text(text,
                                     reply_markup=keyboard,
                                     disable_web_page_preview=True)
    await bot.answer_callback_query(callback.id)


async def spam_or_subscribe_name_id(callback: CallbackQuery, last_ind=-1):
    """Обновление настроек spamming и subscribe для карточек группы/преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, callback.data] = get_callback_values(callback, last_ind)
    type_colomn_name = callback_data_split[-1]
    action_type = type_colomn_name.split('_')[0]
    short_type_name = type_colomn_name.split('_')[-1]
    name_id = callback_data_split[-2]

    result = Update.user_settings_array(user_id,
                                        name_=colomn_name_by_callback.get(type_colomn_name),
                                        value=name_id)

    # удалили подписку
    if type_colomn_name in ('sub_gr', 'sub_tch') and not result:

        # если это карточка с активной основной подпиской, то удаляем её
        if Update.user_settings_value(user_id, 'name_id', name_id, remove_=True):
            Update.user_settings(user_id, 'type_name', 'NULL', convert_val_text=False)

        Update.user_settings_array(user_id,
                                   name_=colomn_name_by_callback.get(f"sp_{short_type_name}"),
                                   value=name_id,
                                   remove_=True)

    elif type_colomn_name in ('sp_gr', 'sp_tch') and result:

        Update.user_settings_array(user_id,
                                   name_=colomn_name_by_callback.get(f"sub_{short_type_name}"),
                                   value=name_id,
                                   remove_=None)

    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=ANSWER_CALLBACK['spam_or_subscribe_name_id'](action_type, result),
                                    show_alert=False)

    if short_type_name == 'gr':
        await group__card(callback)

    elif short_type_name == 'tch':
        await teacher_card(callback)


async def main_subscribe_name_id(callback: CallbackQuery, last_ind=-1):
    """Обновление настроек main_subscribe для карточек группы/преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, callback.data] = get_callback_values(callback, last_ind)
    type_colomn_name = callback_data_split[-1]
    name_id = callback_data_split[-2]

    result = Update.user_settings_value(user_id, 'name_id', name_id)

    # если основная подписка добавлена
    if result:
        Update.user_settings(user_id, 'type_name', type_colomn_name == 'm_sub_gr', convert_val_text=True)
        Update.user_settings_array(user_id,
                                   name_=colomn_name_by_callback.get(type_colomn_name),
                                   value=name_id,
                                   remove_=None)
    else:
        Update.user_settings(user_id, 'type_name', 'NULL', convert_val_text=False)
        Update.user_settings(user_id, 'name_id', 'NULL', convert_val_text=False)

    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=ANSWER_CALLBACK['main_subscribe_name_id'](result),
                                    show_alert=False)

    if type_colomn_name == 'm_sub_gr':
        await group__card(callback)

    elif type_colomn_name == 'm_sub_tch':
        await teacher_card(callback)


async def group__card(callback: CallbackQuery, last_ind=-2):
    """Показать карточку группы"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    group__id = callback_data_split[-1]

    group__user_info = Select.user_info_name_card("group_", user_id, group__id)

    text = ANSWER_TEXT['group__card']
    keyboard = Inline.group__card(group__user_info,
                                  callback_data=callback.data,
                                  last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def teacher_card(callback: CallbackQuery, last_ind=-2):
    """Показать карточку преподавателя"""
    user_id = callback.message.chat.id
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    teacher_id = callback_data_split[-1]

    teacher_user_info = Select.user_info_name_card("teacher", user_id, teacher_id)

    text = ANSWER_TEXT['teacher_card']
    keyboard = Inline.teacher_card(teacher_user_info,
                                   callback_data=callback.data,
                                   last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def week_days_main_timetable(callback: CallbackQuery, last_ind=-1):
    """Показать список дней недели дня получения основного расписания"""
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    text = ANSWER_TEXT['week_days_main_timetable']
    keyboard = Inline.week_days_main_timetable(callback=callback.data,
                                               last_callback_data=last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def get_main_timetable_by_week_day_id(callback: CallbackQuery, last_ind=-1):
    """Получить основное расписание для дня недели"""
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)

    week_day_id = callback_data_split[-1]

    type_name = colomn_name_by_callback.get(callback_data_split[-4])
    name_id = callback_data_split[-3]
    name_ = Select.name_by_id(type_name, name_id)

    data_main_timetable = Select.view_main_timetable(type_name, name_, week_day_id=week_day_id, lesson_type=None)

    if not data_main_timetable:
        week_day = get_week_day_name_by_id(week_day_id, type_case="genitive", bold=False)
        text = ANSWER_CALLBACK['not_timetable_by_week_day'](week_day)
        await bot.answer_callback_query(callback_query_id=callback.id,
                                        text=text)

    else:
        text = get_message_timetable(name_,
                                     get_week_day_name_by_id(week_day_id, type_case='prepositional'),
                                     data_main_timetable,
                                     start_text="Основное расписание на")
        keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

        await callback.message.edit_text(text, reply_markup=keyboard)
        await bot.answer_callback_query(callback.id)


async def months_history_ready_timetable(callback: CallbackQuery, last_ind=-1):
    """Вывести список месяуев"""
    last_callback_data = get_callback_values(callback, last_ind)[-1]

    months_array = Select.months_ready_timetable()

    text = ANSWER_TEXT['months_history_ready_timetable']
    keyboard = Inline.months_ready_timetable(months_array, callback.data, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def dates_ready_timetable(callback: CallbackQuery, last_ind=-1):
    """Вывести список дат"""
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)
    type_name = colomn_name_by_callback.get(callback_data_split[-4])
    name_id = callback_data_split[-3]
    month = callback_data_split[-1]

    name_ = Select.name_by_id(type_name, name_id)

    dates_array = Select.dates_ready_timetable(month)

    text = ANSWER_TEXT['dates_ready_timetable'](name_, month_translate(month))
    keyboard = Inline.dates_ready_timetable(dates_array, callback.data, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@rate_limit(1)
async def download_ready_timetable_txt(callback: CallbackQuery):
    user_id = callback.message.chat.id
    callback_data_split = callback.data.split()

    type_name = colomn_name_by_callback.get(callback_data_split[-5])
    name_id = callback_data_split[-4]
    month = callback_data_split[-2]

    name_ = Select.name_by_id(type_name, name_id)

    text = f"{name_} {month_translate(month)}\n\n"

    user_info = Select.user_info_by_colomn_names(user_id, colomn_names=['view_add', 'view_time'])
    view_add = user_info[0]
    view_time = user_info[1]

    dates_array = Select.dates_ready_timetable(month, type_sort='')

    for date_ in dates_array:
        data_ready_timetable = Select.ready_timetable(type_name, date_, name_)
        date_text = date_.strftime('%d.%m.%Y')
        ready_timetable_message = get_message_timetable(name_,
                                                        date_text,
                                                        data_ready_timetable,
                                                        view_name=False,
                                                        view_add=view_add,
                                                        view_time=view_time)
        text += f"{ready_timetable_message}\n\n"

    file = StringIO(text)
    file.name = f"{name_} {month_translate(month)}.txt"
    await bot.send_document(user_id, file)


async def ready_timetable_by_date(callback: CallbackQuery):
    """Вывести расписание для определённой даты"""
    callback_data_split = callback.data.split()
    type_name = colomn_name_by_callback.get(callback_data_split[-5])
    name_id = callback_data_split[-4]
    date_ = callback_data_split[-1]

    await view_ready_timetable(callback,
                               last_ind=-1,
                               type_name=type_name,
                               name_id=name_id,
                               date_=date_)


async def view_ready_timetable(callback: CallbackQuery, last_ind=-1, type_name=None, name_id=None, date_=None):
    """Показать текущее расписание"""
    [callback_data_split, last_callback_data] = get_callback_values(callback, last_ind)

    if date_ is None:
        date_ = get_day_text()
        if Select.check_filling_table("replacement"):
            """Если таблица с заменами заполнена"""
            date_ = get_day_text(days=1)

    if type_name is None:
        type_name = colomn_name_by_callback.get(callback_data_split[-1])

    if name_id is None:
        name_id = callback_data_split[-2]

    name_ = Select.name_by_id(type_name, name_id)

    data_ready_timetable = Select.ready_timetable(type_name, date_, name_)

    if not data_ready_timetable:
        """Расписание на выбранную дату отсутствует"""
        return await bot.answer_callback_query(callback_query_id=callback.id,
                                               text=ANSWER_CALLBACK['not_ready_timetable'],
                                               show_alert=False)

    text = get_message_timetable(name_, date_, data_ready_timetable)
    keyboard = Inline.get_back_button(last_callback_data, return_keyboard=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


async def view_callback(callback: CallbackQuery):
    """Обработчик нажатий на пустые кнопки"""
    await bot.answer_callback_query(callback_query_id=callback.id,
                                    text=' '.join(callback.data.split()[1:]),
                                    show_alert=True)


async def close(callback: CallbackQuery):
    """Обработать запрос на удаление (закрытие) окна сообщения"""
    await callback.message.delete()


async def help_message(message: Message):
    """Вывести help-сообщение"""
    await message.answer(ANSWER_TEXT['help'])


async def show_keyboard(message: Message):
    await message.answer(text=ANSWER_TEXT['show_keyboard'], reply_markup=Reply.default())


'''
async def bot_blocked(update: types.Update, exception: BotBlocked):
    pass
'''

'''
async def terminated_by_other_get_updates(update: types.Update, exception: TerminatedByOtherGetUpdates):
    await bot.send_message(chat_id=1020624735, text="Запущено 2 экземпляра бота")
'''


def register_user_handlers(dp: Dispatcher):
    # todo: register all user handlers

    global bot
    bot = dp.bot

    dp.register_message_handler(new_user,
                                lambda msg: Select.user_info(user_id=msg.chat.id) is None,
                                content_types=['text'])

    dp.register_message_handler(choise_type_name, commands=['start'], state='*')

    dp.register_callback_query_handler(choise_group__name,
                                       lambda call: check_call(call, ['g_list']),
                                       state=UserStates.choise_type_name)

    dp.register_callback_query_handler(paging_group__list_state,
                                       lambda call: check_call(call, ['g_list'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(paging_group__list,
                                       lambda call: check_call(call, ['g_list'], ind=-2), state='*')

    dp.register_callback_query_handler(choise_teacher_name,
                                       lambda call: check_call(call, ['t_list']),
                                       state=UserStates.choise_type_name)

    dp.register_callback_query_handler(paging_teacher_list_state,
                                       lambda call: check_call(call, ['t_list'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(paging_teacher_list,
                                       lambda call: check_call(call, ['t_list'], ind=-2),
                                       state='*')

    dp.register_message_handler(error_choise_type_name, state=UserStates.choise_type_name)

    dp.register_callback_query_handler(choise_group_,
                                       lambda call: check_call(call, ['gc'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_callback_query_handler(choise_teacher,
                                       lambda call: check_call(call, ['tc'], ind=-2),
                                       state=UserStates.choise_name)

    dp.register_message_handler(error_choise_name, state=UserStates.choise_name)

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

    dp.register_callback_query_handler(spam_or_subscribe_name_id,
                                       lambda call: check_call(call, ['sp_gr', 'sub_gr', 'sp_tch', 'sub_tch']))

    dp.register_callback_query_handler(main_subscribe_name_id,
                                       lambda call: check_call(call, ['m_sub_gr', 'm_sub_tch']))

    dp.register_callback_query_handler(group__card,
                                       lambda call: check_call(call, ['gc'], ind=-2))

    dp.register_callback_query_handler(teacher_card,
                                       lambda call: check_call(call, ['tc'], ind=-2))

    dp.register_callback_query_handler(week_days_main_timetable,
                                       lambda call: check_call(call, ['wdmt']))

    dp.register_callback_query_handler(get_main_timetable_by_week_day_id,
                                       lambda call: check_call(call, ['wdmt'], ind=-2))

    dp.register_callback_query_handler(months_history_ready_timetable,
                                       lambda call: check_call(call, ['mhrt']))

    dp.register_callback_query_handler(dates_ready_timetable,
                                       lambda call: check_call(call, ['mhrt'], ind=-2))

    dp.register_callback_query_handler(download_ready_timetable_txt,
                                       lambda call: check_call(call, ['download_ready_timetable_txt']))

    dp.register_callback_query_handler(ready_timetable_by_date,
                                       lambda call: check_call(call, ['mhrt'], ind=-3))

    dp.register_callback_query_handler(view_ready_timetable,
                                       lambda call: check_call(call, ['g_rt', 't_rt']))

    dp.register_callback_query_handler(view_callback,
                                       lambda call: call.data.split()[0] == '*')

    dp.register_callback_query_handler(close,
                                       lambda call: call.data == 'close', state='*')

    dp.register_message_handler(help_message,
                                commands=['help'],
                                state='*')

    dp.register_message_handler(show_keyboard,
                                commands=['show_keyboard'],
                                state='*')

    # dp.register_errors_handler(terminated_by_other_get_updates, exception=TerminatedByOtherGetUpdates)
