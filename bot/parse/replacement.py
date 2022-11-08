import aiohttp
from bs4 import BeautifulSoup
import requests

from bot.database import Select

from bot.parse.functions import get_full_link_by_part
from bot.parse.functions import get_correct_audience
from bot.parse.functions import convert_lesson_name
from bot.parse.functions import replace_english_letters

from bot.parse.config import main_link_ypec
from bot.parse.config import headers_ypec


def get_part_link_by_day(day):
    """Получить ссылку на страницу сайта"""
    return {'today': 'rasp-zmnow', 'tomorrow': 'rasp-zmnext'}.get(day)


def get_correct_group__name(maybe_group__name):
    """Получить корректное название группы"""
    maybe_group__name = maybe_group__name.replace(' ', '').title()
    return replace_english_letters(maybe_group__name)


def get_correct_teacher_name(maybe_teacher_name):
    """Получить корректное ФИО преподавателя"""
    maybe_teacher_name = maybe_teacher_name.title()
    return replace_english_letters(maybe_teacher_name)


def get_teacher_names_array(one_lesson):
    """Создать массив с ФИО преподавателей"""
    return one_lesson[-1].replace('. ', '.,').split(',')


def get_audience_array(one_lesson):
    """Создать массив аудиторий"""
    audience = replace_english_letters(one_lesson[-2])
    for i in (',', ';'):
        if i in audience:
            return audience.split(i)
    return audience.split()


def get_num_les_array(num_lesson):
    """Получить массив подряд идущих пар"""
    if num_lesson.isdigit() or '-' in num_lesson:
        start = int(num_lesson[0])
        stop = int(num_lesson[-1])
        return list(range(start, stop + 1))
    return [num_lesson]


class Replacements:
    """Класс для обработки замен

    Атрибуты
    --------
    data : list
        массив строчек-пар, готовых к Insert
    date : list
        дата с сайта
    group__names : list
        кортеж групп
    teacher_names : set
        кортеж преподавателей
    lesson_names : set
        кортеж названий пар
    audience_names : set
        кортеж названий аудиторий

    """

    def __init__(self):
        self.data = []
        self.date = None
        self.week_lesson_type = None
        self.group__names = set()
        self.lesson_names = set()
        self.teacher_names = set()
        self.audience_names = set()

        self.method = "async"

    def get_date(self, soup):
        """Получить дату с сайта"""
        date_text = soup.find("div", itemprop="articleBody").find("strong").text.lower()
        self.date = date_text.split()[2]
        self.week_lesson_type = True if "числ" in date_text else False if "знам" in date_text else None

    async def parse(self, day='tomorrow', ):
        """Парсим замены и заносим данные в массив self.data"""
        part_link = get_part_link_by_day(day)
        url = get_full_link_by_part(main_link_ypec, part_link)

        if self.method == "async":
            session = aiohttp.ClientSession()
            result = await session.post(url, headers=headers_ypec)
            soup = BeautifulSoup(await result.text(), 'lxml')
            await session.close()
        else:
            result = requests.post(url, headers=headers_ypec, verify=True)
            soup = BeautifulSoup(result.text, 'lxml')

        self.table_handler(soup)

    def table_handler(self, soup):
        group__name = None

        table_soup = soup.find('table', class_='isp')
        self.get_date(soup)
        rows = table_soup.find_all('tr')[1:]

        # Обрабатываем первую строчку
        first_row = table_soup.find_all('td')[6:12]
        new_tr = soup.new_tag("tr")

        for td in first_row:
            new_tr.append(td)

        rows.insert(0, new_tr)

        for tr in rows:
            """Перебираем строчки таблицы"""
            one_td_array = tr.find_all('td')

            if not one_td_array:
                continue

            if not one_td_array[0].get("rowspan") is None:
                maybe_group__name = get_correct_group__name(one_td_array[0].text)
                group__name = Select.query_info_by_name('group_',
                                                        info='name',
                                                        value=maybe_group__name)[0]

                if group__name is not None:
                    one_td_array = one_td_array[1:]

            one_lesson = [td.text.strip() for td in one_td_array]

            try:
                num_lesson = one_lesson[0]
                lesson_by_main_timetable = replace_english_letters(one_lesson[1])
                rep_lesson = one_lesson[-3]

                replace_for_lesson = rep_lesson
                # Если нет номера пары (практика), то оставляем строку с парой как есть
                if num_lesson != '':
                    replace_for_lesson = convert_lesson_name(rep_lesson)

                audience_array = get_audience_array(one_lesson)
                teacher_names_array = get_teacher_names_array(one_lesson)
                num_les_array = get_num_les_array(num_lesson)

                """Перебираем номера пар"""
                for num_lesson in num_les_array:

                    for teacher_name in teacher_names_array:
                        ind = teacher_names_array.index(teacher_name)
                        teacher_name_corrected = get_correct_teacher_name(teacher_name)

                        maybe_teacher_name = Select.query_info_by_name('teacher',
                                                                       info='name',
                                                                       value=teacher_name_corrected)[0]

                        if maybe_teacher_name is None:
                            maybe_teacher_name = teacher_name_corrected
                            if len(maybe_teacher_name) > 5:
                                self.teacher_names.add(maybe_teacher_name)

                        if len(audience_array) == 1:
                            ind = 0

                        # необходимо при наличии одного учителя, но нескольких кабинетов добавлять все кабинеты
                        audience = None
                        if audience_array:
                            audience = get_correct_audience(audience_array[ind])

                        one_lesson_data = (group__name,
                                           num_lesson,
                                           lesson_by_main_timetable,
                                           replace_for_lesson,
                                           maybe_teacher_name,
                                           audience)

                        self.data.append(one_lesson_data)

                        if replace_for_lesson not in ('Нет', 'По расписанию'):
                            self.lesson_names.add(replace_for_lesson)

                        self.audience_names.add(audience)

            except IndexError:
                ...
