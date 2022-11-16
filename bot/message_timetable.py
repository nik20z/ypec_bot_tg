import aiogram.utils.markdown as fmt

from bot.config import CALL_SCHEDULE
from bot.functions import get_week_day_id_by_date_


def get_one_time(type_week_day: str,
                 num_les: str,
                 ind: int = 0):
    """Получить время звонка по типу дня недели, номеру пары и индексу"""
    try:
        return CALL_SCHEDULE[type_week_day].get(num_les)[ind]
    except TypeError:
        return None


def get_time_text(time_str: str, format_str: str):
    """Вернуть отформатированную строку с временем (по шаблону)"""
    if time_str is None:
        return ""
    return format_str.format(time_str)


def get_time_for_timetable(date_str: str, num_lesson_array: list):
    """Получить время начала и окончания занятий"""
    #num_lesson_array = [int(num) for x in num_lesson_array for num in x]
    start_num_les = min(num_lesson_array)
    stop_num_les = max(num_lesson_array)

    week_day_id = get_week_day_id_by_date_(date_str)
    type_week_day = 'weekday' if week_day_id in range(6) else 'saturday'

    start_time = get_one_time(type_week_day, start_num_les)
    stop_time = get_one_time(type_week_day, stop_num_les, ind=-1)

    start_time_text = get_time_text(start_time, "С {0}")
    stop_time_text = get_time_text(stop_time, "До {0}")

    return f"{start_time_text} {stop_time_text}"


def get_joined_text_by_list(array_: list, char_: str = ' / '):
    """Преобразуем список в строку элементов, записанных через разделитель"""
    return char_.join([x for x in array_ if x is not None])


def get_paired_num_lesson(num_array: list):
    """Объединяем пары"""
    start_num = min(num_array)
    stop_num = max(num_array)
    if start_num != stop_num:
        return f"{start_num}-{stop_num}"
    return start_num


class MessageTimetable:
    def __init__(self,
                 name_: str,
                 date_str: str,
                 data_ready_timetable: list,
                 start_text: str = "Расписание на ",
                 view_name: bool = True,
                 view_add: bool = True,
                 view_time: bool = False,
                 format_: bool = True,
                 type_format: str = "message",
                 format_timetable: str = "default"):
        self.name_ = name_
        self.date_str = date_str
        self.data_ready_timetable = data_ready_timetable
        self.start_text = start_text
        self.view_name = view_name
        self.view_add = view_add
        self.view_time = view_time
        self.format_ = format_
        self.type_format = type_format
        self.format_timetable = format_timetable

        self.message = ""
        self.num_lesson_array = []

    def check_empty(self):
        """Проверка на пустоту"""
        if not self.data_ready_timetable:
            if self.format_timetable == "default":
                self.message += f"Расписание для {self.name_}" \
                                f"\n" \
                                f"На {self.date_str} отсутствует"

            elif self.format_timetable == "only_date":
                self.message += self.date_str

            elif self.format_timetable == "empty":
                self.message += ""

            return True
        return False

    def check_view_name(self):
        """Если необходимо отображать name_"""
        add_name_text = ""
        if self.view_name:
            if self.format_:
                add_name_text = f"<b>{self.name_}</b>\n"
            else:
                add_name_text = f"{self.name_}\n"

        self.message += f"{add_name_text}{self.start_text}{self.date_str}\n"

    def formatting_line_text(self,
                             one_line: list,
                             line_text: str):
        """Получаем линию-строку для одной пары"""
        if not self.format_ or one_line[2][0] is None:
            """Если не включено форматирование текста"""
            self.message += line_text
        else:
            if one_line[2][0]:
                """Если числитель"""
                if self.type_format == "message":
                    self.message += fmt.hunderline(line_text)
                elif self.type_format == "txt":
                    self.message += f"Числитель {line_text}"
            else:
                """Если знаменатель"""
                if self.type_format == "message":
                    self.message += fmt.hcode(line_text)  # hitalic
                elif self.type_format == "txt":
                    self.message += f"Знаменатель {line_text}"

    def check_view_time(self):
        """Добавляем время начала и окончания занятий при необходимости"""
        if self.view_time:
            self.message += get_time_for_timetable(self.date_str, self.num_lesson_array)

    def create_d_lessons(self):
        """Создаём словарь, в котором ключ - номер пары, а значение - массив массивов пар"""
        d_lessons = {}
        for one_line in self.data_ready_timetable:
            num_lesson = one_line[0]
            last_num = None
            num_array = []

            for num in num_lesson:
                self.num_lesson_array.append(num)

                if last_num is None or int(num)-1 == int(last_num):
                    num_array.append(num)

                else:
                    new_num_lesson = get_paired_num_lesson(num_array)
                    if new_num_lesson not in d_lessons:
                        d_lessons[new_num_lesson] = []
                    d_lessons[new_num_lesson].append(one_line[1:])
                    num_array = [num]

                if num == num_lesson[-1]:
                    new_num_lesson = get_paired_num_lesson(num_array)
                    if new_num_lesson not in d_lessons:
                        d_lessons[new_num_lesson] = []
                    d_lessons[new_num_lesson].append(one_line[1:])

                last_num = num

        return d_lessons

    def get(self):
        """Получаем текстовое представление расписания по заданным параметрам"""

        if self.check_empty():
            return self.message

        """Добавляем name_ группы при необходимости"""
        self.check_view_name()

        """Создаём словарь спаренных пар (1-2 и тд)"""
        d_lessons = self.create_d_lessons()

        """Перебираем массивы пар"""
        for num_lesson, one_line_array in sorted(d_lessons.items()):

            for one_line in one_line_array:
                lesson_text = one_line[0][0]
                json_group_or_teacher_name_and_audience = one_line[1]

                group_or_teacher_name = json_group_or_teacher_name_and_audience.keys()
                audience = json_group_or_teacher_name_and_audience.values()

                """Составляем строку"""
                num_text = "" if num_lesson == '' else f"{num_lesson})"
                group_or_teacher_name_text = get_joined_text_by_list(group_or_teacher_name)
                audience_text = get_joined_text_by_list(audience)

                add_group_or_teacher_name_text = f"({group_or_teacher_name_text})" if self.view_add else ""

                line_text = f"{num_text} {lesson_text} {audience_text} {add_group_or_teacher_name_text}\n"

                self.formatting_line_text(one_line, line_text)

        """Добавляем время начала и окончания при необходимости"""
        self.check_view_time()

        return self.message
