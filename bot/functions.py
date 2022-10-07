from aiogram.types import CallbackQuery
import aiogram.utils.markdown as fmt
from datetime import datetime, date, timedelta
import requests

from bot.config import CALL_SCHEDULE


def month_translate(month_name: str):
    """Перевести короткое название месяца на русский язык"""
    month_d = {'jan': 'Январь',
               'feb': 'Февраль',
               'mar': 'Март',
               'apr': 'Апрель',
               'may': 'Май',
               'june': 'Июнь',
               'jun': 'Июнь',
               'july': 'Июль',
               'jul': 'Июнь',
               'aug': 'Август',
               'sep': 'Сентябрь',
               'oct': 'Октябрь',
               'now': 'Ноябрь',
               'dec': 'Декабрь'
               }
    return month_d.get(month_name.lower())


def get_week_day_name_by_id(wee_day_id: int, type_case="default", bold=True):
    """Получить название дня недели по id"""
    week_array = {'default': ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'],
                  'genitive': ['понедельника', 'вторника', 'среды', 'четверга', 'пятницы', 'субботы'],
                  'prepositional': ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу']}
    week_day_text = week_array[type_case][int(wee_day_id)].title()
    if bold:
        return f"<b>{week_day_text}</b>"
    return week_day_text


def get_joined_text_by_list(array_: list, char_=' / '):
    return char_.join([x for x in array_ if x is not None])


def get_message_timetable(name_: str,
                          date_str: str,
                          data_ready_timetable: list,
                          start_text="Расписание на ",
                          view_name=True,
                          view_add=True,
                          view_time=False,
                          formated=True):
    """Составить сообщение с расписанием"""
    if not data_ready_timetable:
        return f"Расписание для {name_}" \
               f"\n" \
               f"На {date_str} отсутствует"

    add_name_text = ""
    num_lesson_array = []

    if view_name:
        """Если необходимо отображать name_"""
        if formated:
            add_name_text = f"<b>{name_}</b>\n"
        else:
            add_name_text = f"{name_}\n"

    text = f"{add_name_text}{start_text}{date_str}\n"

    """Перебираем массивы пар"""
    for one_line in data_ready_timetable:
        num = one_line[0]
        lesson_text = one_line[1][0]
        json_group_or_teacher_name_and_audience = one_line[2]

        num_lesson_array.append(num)

        group_or_teacher_name = json_group_or_teacher_name_and_audience.keys()
        audience = json_group_or_teacher_name_and_audience.values()

        # соединяем повторяющиеся пары
        start_num = int(num[0])
        stop_num = int(num[-1])

        if len(num) > 1 and list(map(int, num)) == list(range(start_num, stop_num + 1)):
            num = [f"{start_num}-{stop_num}"]

        # перебираем номера пар
        for num_text in num:

            group_or_teacher_name_text = get_joined_text_by_list(group_or_teacher_name)
            audience_text = get_joined_text_by_list(audience)

            add_group_or_teacher_name_text = f"({group_or_teacher_name_text})" if view_add else ""

            line_text = f"{num_text}) {lesson_text} {audience_text} {add_group_or_teacher_name_text}\n"

            if not formated or one_line[3][0] is None:
                """Если включено форматирование текста"""
                text += line_text
            else:
                if one_line[3][0]:
                    """Если числитель"""
                    text += fmt.hunderline(line_text)
                else:
                    """Если знаменатель"""
                    text += fmt.hcode(line_text)  # hitalic

    if view_time:
        text += get_time_for_timetable(date_str, num_lesson_array)

    return text


def get_time_for_timetable(date_str: str, num_lesson_array: list):
    """Получить время начала и окончания занятий"""
    num_lesson_array = [num for x in num_lesson_array for num in x]
    start_num_les = min(num_lesson_array)
    stop_num_les = max(num_lesson_array)

    week_day_id = get_week_day_id_by_date_(date_str)
    type_week_day = 'weekday' if week_day_id in range(6) else 'saturday'

    times_week_day = CALL_SCHEDULE[type_week_day]

    start_time = times_week_day.get(start_num_les)[0]
    stop_time = times_week_day.get(stop_num_les)[-1]

    return f"С {start_time} до {stop_time}"


def check_call(callback: CallbackQuery, commands: list, ind=-1):
    """Проверка вхождения команды в callback по индексу"""
    callback_data_split = callback.data.split()
    try:
        return callback_data_split[ind] in commands
    except IndexError:
        return False


def get_callback_values(callback: CallbackQuery, last_ind: int):
    """Получить callback_data_split и last_callback_data с ограничением по индексу"""
    callback_data_split = callback.data.split()
    last_callback_data = ' '.join(callback_data_split[:last_ind])
    return callback_data_split, last_callback_data


colomn_name_by_callback = {'sp_gr': 'spam_group_',
                           'sub_gr': 'group_',
                           'sp_tch': 'spam_teacher',
                           'sub_tch': 'teacher',
                           'm_sub_gr': 'group_',
                           'm_sub_tch': 'teacher',
                           'g_rt': 'group_',
                           'g_list': 'group_',
                           'gc': 'group_',
                           't_rt': 'teacher',
                           't_list': 'teacher',
                           'tc': 'teacher'
                           }


def get_day_text(date_=None, days=0, delete_sunday=True, format_str="%d.%m.%Y"):
    """Получить отформатированную дату"""
    if date_ is None:
        date_ = date.today()

    if delete_sunday and date_.weekday() == 5:
        days = 2

    return (date_ + timedelta(days=days)).strftime(format_str)


def get_next_check_time(array_times: list, func_name: str):
    """Расчет времени до следующего цикла в зависимости от названия функции"""

    delta = 0
    one_second = 0

    for t in array_times[func_name]:
        now = datetime.now()
        one_second = round(now.microsecond / 1000000)

        check_t = datetime.strptime(t, "%H:%M")

        delta = timedelta(hours=now.hour - check_t.hour,
                          minutes=now.minute - check_t.minute,
                          seconds=now.second - check_t.second)

        seconds = delta.total_seconds()
        if seconds < 0:
            return seconds * (-1) + one_second

    seconds = (timedelta(hours=24) - delta).total_seconds()
    return seconds + one_second


def get_full_link_by_part(main_link: str, part_link: str):
    """Получить готовую ссылку"""
    return f"{main_link}/{part_link}"


def get_correct_audience(audience: str):
    """Получить отформатированное название аудитории"""
    audience = audience.strip()
    if audience in ("&nbsp", "''", ""):
        return None

    if audience.isdigit():
        if int(audience) >= 100:
            return f"А-{audience}"
        elif 10 <= int(audience) <= 50 and len(audience) <= 2:
            return f"Б-{audience}"

    return audience.title()


def get_week_day_id_by_date_(date_: str, format_str="%d.%m.%Y"):
    """Получить номер недели по дате"""
    return datetime.strptime(date_, format_str).weekday()


def convert_timetable_to_dict(timetable: list):
    """Конвертируем массив со строчками расписания в словарь"""
    timetable_d = {}

    for one_lesson in timetable:
        num_lesson = one_lesson[0]
        if num_lesson not in timetable_d:
            timetable_d[num_lesson] = []
        lesson_name = one_lesson[1][0]
        teacher_name_array = one_lesson[2]
        audience_name_array = one_lesson[3]
        timetable_d[num_lesson].append([lesson_name, teacher_name_array, audience_name_array])

    return timetable_d


def get_rub_balance(login: str, api_access_token: str):
    """Получить баланс QIWI Кошелька"""
    s = requests.Session()
    s.headers['Accept'] = 'application/json'
    s.headers['authorization'] = 'Bearer ' + api_access_token
    b = s.get(f"https://edge.qiwi.com/funding-sources/v2/persons/{login}/accounts")
    s.close()

    # все балансы
    balances = b.json()['accounts']

    # рублевый баланс
    rub_alias = [x for x in balances if x['alias'] == 'qw_wallet_rub']
    rub_balance = rub_alias[0]['balance']['amount']

    return rub_balance


def convert_lesson_name(lesson_name):
    lesson_name = lesson_name.replace(' ,', ', ')

    lesson_name = ', '.join(lesson_name.split(','))
    lesson_name = ' '.join(lesson_name.split('('))

    for key, val in {'.': '', ',': '', '2гр': '2 гр'}.items():
        lesson_name = lesson_name.replace(key, val)

    lesson_name = ' '.join(lesson_name.split())

    return lesson_name.strip()
