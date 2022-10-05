from bs4 import BeautifulSoup
import requests

from bot.database import Select

from bot.functions import get_full_link_by_part
from bot.functions import get_correct_audience

from bot.parse.config import main_link_ypec
from bot.parse.config import headers_ypec


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
        self.get_part_link_by_day = lambda day: {'today': 'rasp-zmnow',
                                                 'tomorrow': 'rasp-zmnext'}.get(day, 'tomorrow')

        self.get_correct_group__name = lambda s: s.strip().replace(' ', '')

        self.data = []
        self.date = None
        self.week_lesson_type = None
        self.group__names = set()
        self.lesson_names = set()
        self.teacher_names = set()
        self.audience_names = set()

    def get_date(self, soup):
        """Получить дату с сайта"""
        date_text = soup.find("div", itemprop="articleBody").find("strong").text.lower()
        self.date = date_text.split()[2]
        self.week_lesson_type = True if "числ" in date_text else False if "знам" in date_text else None

    def parse(self, day='tomorrow'):
        """Парсим замены и заносим данные в массив self.data

            Параметры:
                day (str): день, для которого необходимо спарсить замены

            Возвращаемое значение:
                None
        """
        part_link = self.get_part_link_by_day(day)
        url = get_full_link_by_part(main_link_ypec, part_link)

        r = requests.post(url, headers=headers_ypec, verify=True)
        soup = BeautifulSoup(r.text, 'lxml')
        table_soup = soup.find('table', class_='isp')

        self.get_date(soup)

        group__name = None

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
                maybe_group__name = self.get_correct_group__name(one_td_array[0].text)
                group__name = Select.query_info_by_name('group_',
                                                        info='name',
                                                        value=maybe_group__name)

                if group__name is not None:
                    one_td_array = one_td_array[1:]

            one_lesson = [td.text.strip() for td in one_td_array]

            try:
                num_lesson = one_lesson[0]
                lesson_by_main_timetable = one_lesson[1]
                rep_lesson = one_lesson[-3]

                try:
                    replace_for_lesson = rep_lesson[0].upper() + rep_lesson[1:]
                except IndexError:
                    replace_for_lesson = rep_lesson

                audience_array = one_lesson[-2].split(',')
                teacher_names_array = one_lesson[-1].replace('. ', '.,').split(',')

                if num_lesson.isdigit() or '-' in num_lesson:
                    start = int(num_lesson[0])
                    stop = int(num_lesson[-1])
                    num_les_array = list(range(start, stop + 1))
                else:
                    num_les_array = [num_lesson]

                for num_lesson in num_les_array:

                    for teacher_name in teacher_names_array:
                        ind = teacher_names_array.index(teacher_name)
                        teacher_name_corrected = teacher_name.strip().title()

                        maybe_teacher_name = Select.query_info_by_name('teacher',
                                                                       info='name',
                                                                       value=teacher_name_corrected)

                        if maybe_teacher_name is None:
                            maybe_teacher_name = teacher_name_corrected
                            if len(maybe_teacher_name) > 5:
                                self.teacher_names.add(maybe_teacher_name)

                        if len(audience_array) == 1:
                            ind = 0

                        # необходимо при наличии одного учителя, но нескольких кабинетах добавлять все кабинеты

                        audience = get_correct_audience(audience_array[ind])

                        one_lesson_data = (group__name,
                                           num_lesson,
                                           lesson_by_main_timetable,
                                           replace_for_lesson,
                                           maybe_teacher_name,
                                           audience)

                        # print("one_lesson_data", one_lesson_data)

                        self.data.append(one_lesson_data)

                        if replace_for_lesson not in ('Нет', 'По расписанию'):
                            self.lesson_names.add(replace_for_lesson)

                        self.audience_names.add(audience)

            except IndexError:
                ...
