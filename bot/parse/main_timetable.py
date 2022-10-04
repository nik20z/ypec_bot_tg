from bs4 import BeautifulSoup
import requests
import time

from bot.functions import get_full_link_by_part
from bot.functions import get_correct_audience

from bot.parse.config import main_link_ypec
from bot.parse.config import headers_ypec


class MainTimetable:
    """Класс для обработки основного расписания

        Атрибуты
        --------
        data : list
            массив строчек-пар, готовых к Insert
        group__names : list
            список групп
        teacher_names : list
            списов преподавателей
        lesson_names : set
            кортеж названий пар
        audience_names : set
            кортеж названий аудиторий

        """

    def __init__(self):
        self.days_week = {'понедельник': 0,
                          'вторник': 1,
                          'среда': 2,
                          'четверг': 3,
                          'пятница': 4,
                          'суббота': 5,
                          'воскресенье': 6
                          }

        self.get_lesson_type = lambda td: {'dfdfdf': True, 'a3a5a4': False}.get(td.get('bgcolor'), None)

        self.type_names = ['group_', 'teacher']

        self.data = []
        self.group__names = []
        self.teacher_names = []
        self.lesson_names = set()
        self.audience_names = set()

        self.session = requests.Session()

    def get_data_post(self, type_name: str, name_: str):
        """Формирование data для запроса страницы с расписанием"""
        data_name_ = name_
        if type_name == 'teacher':
            """Если работаем с преподавателем, то на сервер отправляется не его ФИО, а номер"""
            data_name_ = self.get_info_by_type_name(type_name, 'array_names').index(name_) + 1
        short_type_name = self.get_info_by_type_name(type_name, 'short_type_name')
        data_post = {short_type_name: data_name_}
        return data_post

    def get_array_names_by_type_name(self, type_name=None):
        """Получить массив с названиями групп или ФИО преподавателей"""
        if type_name is None:
            for type_name in self.type_names:
                self.get_array_names_by_type_name(type_name=type_name)

        else:
            part_link = self.get_info_by_type_name(type_name, get_='part_link')
            url = get_full_link_by_part(main_link_ypec, part_link)

            r = requests.get(url, verify=True)
            soup = BeautifulSoup(r.text, 'lxml')

            array_names = [x.text.strip() for x in soup.find('select').find_all('option')][1:]

            if type_name == 'group_':
                self.group__names = array_names
            elif type_name == 'teacher':
                self.teacher_names = array_names

            return array_names

    def get_info_by_type_name(self, type_name, get_='part_link'):
        """Получить по типу профиля информацию:"""
        data_by_type_name = {'group_': ['rasp-s', 'grp', self.group__names],
                             'teacher': ['rasp-sp', 'prep1', self.teacher_names]}
        ind = ['part_link', 'short_type_name', 'array_names'].index(get_)
        return data_by_type_name[type_name][ind]

    def parse(self, type_name=None, names=None):
        """Парсим расписание"""
        if names is None:
            names = []
        part_link = self.get_info_by_type_name(type_name, get_='part_link')
        url = get_full_link_by_part(main_link_ypec, part_link)

        if type_name is None:
            """парсим все типы - и группы и преподавателей и перезапускаем функцию"""
            for type_name_for in self.type_names:
                self.parse(type_name=type_name_for)

        elif not names:
            """Если не указан массив наимеований, то получаем его и перезапускаем функцию"""
            array_names = self.get_array_names_by_type_name(type_name=type_name)
            self.parse(type_name=type_name, names=array_names)

        else:

            for name_ in names:
                print("name_", name_)

                data_post = self.get_data_post(type_name, name_)

                self.table_handler(url, data_post, type_name, name_)

                time.sleep(2)

    def table_handler(self,
                      url: str,
                      data_post: dict,
                      type_name: str,
                      name_: str):
        """Обрабатываем таблицу с расписанием и заносим данные в self.data

            Параметры:
                url (str): ссылка для парсинга
                data_post (dict): данные для запроса
                type_name (str): тип профиля
                name_ (str): название группы/преподавателя

            Возвращаемое значение:
                None
        """

        with self.session.post(url, data_post, headers=headers_ypec) as response:

            soup = BeautifulSoup(response.text, 'lxml')
            table_soup = soup.find('table', class_='isp3')

            week_day_id = None
            last_num_lesson = None

            if table_soup is None:
                return

            for tr in table_soup.find_all('tr')[1:]:
                one_lesson = []
                state_lesson = True

                one_td_array = tr.find_all('td')

                if not tr.get("class") is None:
                    maybe_week_day = one_td_array[0].text.strip().lower()
                    week_day_id = self.days_week.get(maybe_week_day, None)
                    one_td_array = one_td_array[1:]

                for td in one_td_array:
                    if td.get('bgcolor') == 'lime':
                        state_lesson = False
                    one_lesson.append(td.text.strip())

                num_lesson = one_lesson[0]
                lesson_type = self.get_lesson_type(td)
                audience_split = one_lesson[-1].split(',')

                if type_name == 'teacher':
                    lesson_name = one_lesson[-2].replace(' ,', ', ')
                    teacher_or_group_name_split = [one_lesson[-3]]
                else:
                    lesson_name = one_lesson[-3].replace(' ,', ', ')
                    teacher_or_group_name_split = one_lesson[-2].split('/')

                if not num_lesson[0].isdigit() or (len(num_lesson) > 2 and num_lesson[2].isalpha()):
                    num_lesson = last_num_lesson

                ind = 0
                for tgn in teacher_or_group_name_split:
                    teacher_or_group_name = tgn.strip().title()
                    audience = get_correct_audience(audience_split[ind])
                    ind = -1
                    one_lesson_data = (name_,
                                       week_day_id,
                                       state_lesson,
                                       lesson_type,
                                       num_lesson,
                                       lesson_name.strip(),
                                       teacher_or_group_name,
                                       audience)
                    if type_name == 'teacher':
                        one_lesson_data = (teacher_or_group_name,
                                           week_day_id,
                                           state_lesson,
                                           lesson_type,
                                           num_lesson,
                                           lesson_name.strip(),
                                           name_,
                                           audience)

                    self.data.append(one_lesson_data)

                    self.audience_names.add(audience)

                self.lesson_names.add(lesson_name)

                last_num_lesson = num_lesson