from bs4 import BeautifulSoup
import datetime
import requests
import time

from bot.functions import get_day_text

from .config import main_link_ypec, headers_ypec


def get_week_day_id_by_date_(date_, format_str="%d.%m.%Y"):
    return datetime.datetime.strptime(date_, format_str).weekday()


def get_full_link_by_part(main_link, part_link):
    return f"{main_link}/{part_link}"


def get_correct_audience(audience):
    audience = audience.strip()
    if audience in ("&nbsp", "''", ""):
        return None

    if audience.isdigit():
        if int(audience) >= 100:
            return f"А-{audience}"
        elif 10 <= int(audience) <= 50 and len(audience) <= 2:
            return f"Б-{audience}"

    return audience.title()


def convert_timetable_to_dict(timetable):
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


def get_rub_balance(login, api_access_token):
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


class MainTimetable:
    print("MainTimetable")
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

    def __init__(self, Select):
        self.get_part_link_by_day = lambda day: {'today': 'rasp-zmnow',
                                                 'tomorrow': 'rasp-zmnext'}.get(day, 'tomorrow')

        self.get_correct_group__name = lambda s: s.strip().replace(' ', '')

        self.Select = Select

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
                day (str): день, для которого неообходимо спарсить замены

            Возвращаемое значение:
                None
        """
        part_link = self.get_part_link_by_day(day)
        url = get_full_link_by_part(main_link_ypec, part_link)

        r = requests.post(url, verify=True)
        # r = open('index.html', 'rb').read()
        soup = BeautifulSoup(r.text, 'lxml')  # r.text    lxml
        table_soup = soup.find('table', class_='isp')

        self.get_date(soup)

        group__name = None

        # print(table_soup.find('tr'))
        """
        Таблица на сайте составлена неправильно - первая строчка не имеет тега <tr></tr>
        """

        for tr in table_soup.find_all('tr')[1:]:
            """Перебираем строчки таблицы"""
            one_td_array = tr.find_all('td')

            if not one_td_array:
                continue

            if not one_td_array[0].get("rowspan") is None:
                maybe_group__name = self.get_correct_group__name(one_td_array[0].text)
                group__name = self.Select.query_info_by_name('group_', info='name', value=maybe_group__name)

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

                        maybe_teacher_name = self.Select.query_info_by_name('teacher', info='name',
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


class TimetableHandler:
    """Класс-обработчик

        Атрибуты
        --------
        mt : class
            class MainTimetable
        rep : class
            class Replacement
        ready_timetable_data : list
            массив со строчками с готовым расписанием
        date_replacement : str
            завтрашняя дата
        week_lesson_type : int
            id завтрашнего дня недели
        group__names : list
            кортеж групп
        teacher_names : set
            кортеж преподавателей

        """

    def __init__(self, Table, Insert, Update, Select):
        self.Table = Table
        self.Insert = Insert
        self.Update = Update
        self.Select = Select

        self.ready_timetable_data = []
        self.date_replacement = get_day_text(days=1)
        self.week_lesson_type = get_week_day_id_by_date_(self.date_replacement)

        self.mt = MainTimetable()
        self.rep = Replacements(self.Select)

        self.group__names = self.Select.all_info("group_", colomn_name="group__name")
        if not self.group__names:
            self.group__names = self.mt.get_array_names_by_type_name('group_')
            self.Insert.group_(self.mt.group__names)

        self.teacher_names = self.Select.all_info("teacher", colomn_name="teacher_name")
        if not self.teacher_names:
            self.teacher_names = self.mt.get_array_names_by_type_name('teacher')
            self.Insert.teacher(self.mt.teacher_names)

        self.lesson_names = set()

    def get_main_timetable(self, type_name=None, names=None):
        """Получаем основное расписание"""

        if names is None:
            names = []

        self.mt.group__names = self.group__names
        self.mt.teacher_names = self.teacher_names

        self.mt.data.clear()
        self.Table.delete('main_timetable')

        self.mt.parse(type_name=type_name, names=names)

        self.Insert.lesson(self.mt.lesson_names)
        self.Insert.audience(self.mt.audience_names)
        self.Insert.main_timetable(self.mt.data)

    def get_replacement(self, day="tomorrow"):
        """Получаем замены"""
        self.rep.group__names = self.group__names

        self.rep.data.clear()

        self.rep.parse(day=day)
        self.date_replacement = self.rep.date
        self.week_lesson_type = self.rep.week_lesson_type

        # если замен нет
        if not self.rep.data:
            self.Table.delete('replacement')
            self.Table.delete('replacement_temp')
            return "NO"

        self.Insert.lesson(self.rep.lesson_names)
        self.Insert.teacher(self.rep.teacher_names)
        self.Insert.audience(self.rep.audience_names)

        # если есть замены, но таблица с ними пуста
        if self.Select.check_filling_table('replacement'):
            self.Insert.replacement(self.rep.data)
            return "NEW"

        else:
            # если замены есть, то перезаписываем их
            self.Table.delete('replacement')
            self.Insert.replacement(self.rep.data)

            return "UPDATE"

    def get_ready_timetable(self,
                            date_=None,
                            type_name='group_',
                            names_array=None,
                            lesson_type=True):
        """Получаем готовое расписание
        :param date_: дата, для которой будет составлено расписание
        :param type_name: тип профиля
        :param names_array: массив наименований групп/преподавателей
        :param lesson_type: тип недели (числитель/знаменатель)
        :return: None
        """

        if names_array is None:
            names_array = []

        if date_ is None:
            date_ = get_day_text(days=1)

        week_day_id = get_week_day_id_by_date_(date_)

        self.ready_timetable_data.clear()

        self.replacements_join_timetable(date_=date_,
                                         type_name=type_name,
                                         names_array=names_array,
                                         week_day_id=week_day_id,
                                         lesson_type=lesson_type)

        self.Insert.lesson(self.lesson_names)
        self.Insert.ready_timetable(self.ready_timetable_data)

    def get_names_array_by_type_name(self, type_name):
        """Получить массив наименований по пиру профиля"""
        if type_name == 'group_':
            return self.group__names

        elif type_name == 'teacher':
            return self.teacher_names

    def replacements_join_timetable(self,
                                    date_=None,
                                    type_name='group_',
                                    names_array=None,
                                    week_day_id=0,
                                    lesson_type=True):
        """
        Соединяем замены с основным расписанием
        :param date_: дата, для которой будет составлено расписание
        :param type_name: тип профиля
        :param names_array: массив наименований групп/преподавателей
        :param week_day_id: id дня недели
        :param lesson_type: тип недели (числитель/знаменатель)
        :return: None
        """

        if names_array is None:
            names_array = []

        if not names_array:
            names_array = self.get_names_array_by_type_name(type_name)

        for name_ in names_array:

            timetable = self.Select.main_timetable(type_name=type_name,
                                                   name_=name_,
                                                   week_day_id=week_day_id,
                                                   lesson_type=lesson_type)

            replacement = self.Select.replacement(type_name, name_)

            timetable_dict = convert_timetable_to_dict(timetable)

            last_num_lesson = None
            #last_name = None

            for rep_val in replacement:
                """Перебираем строчки с заменами"""

                num_lesson = rep_val[0]
                lesson_by_main_timetable = rep_val[1][0]
                replace_for_lesson = rep_val[2][0]
                rep_name = rep_val[3][0]
                rep_audience_array = rep_val[4]

                if num_lesson in timetable_dict:
                    """Если номер замены есть в оосновном расписании"""

                    """Перебираем все пары для определённого номера пары"""
                    for les in timetable_dict[num_lesson]:

                        """Индекс пары в массиве пар"""
                        ind = timetable_dict[num_lesson].index(les)
                        name_array = les[-2]

                        if 'по расписанию' in replace_for_lesson.lower():
                            """Обработчик ---по расписанию---"""

                            if rep_name in name_array:
                                """Если есть совпадение с преподавателем"""

                                if rep_name == name_array[ind]:
                                    """Если для данной пары есть"""
                                    timetable_dict[num_lesson][ind][-3] += \
                                        replace_for_lesson.lower().split('по расписанию')[-1]
                                    # timetable_dict[num_lesson][ind][-2] = [rep_name]
                                    timetable_dict[num_lesson][ind][-1] = rep_audience_array

                            # учесть ситуацию, когда предмет не меняется, но меняется препод!!!!
                            # учесть ситуацию, когда в основном расписании нет преподов, но он указан в заменах

                            elif list(set(name_array)) == [None]:
                                """Если в оснвоном расписании не указан преподаватель"""
                                timetable_dict[num_lesson] = [[timetable_dict[num_lesson][ind][-3],
                                                               [rep_name],
                                                               rep_audience_array]]

                            elif rep_name is None:
                                """Если в заменах не указан преподаватель """
                                timetable_dict[num_lesson][ind][-1] = rep_audience_array

                        elif replace_for_lesson.strip().lower() == 'нет':
                            """Если пару отменили"""

                            if len(name_array) == 1 and last_num_lesson != num_lesson:
                                """Если пару ведёт один преподаватель и номер в прошлой итерации не равен текущему номеру пары"""
                                del timetable_dict[num_lesson]
                                break

                            else:
                                '''
                                это развилка для ситуаций, когда в заменах одна пара по расписанию, а другая отменяется
                                проблема моего костыля в том, что при мелейшей ошибке - код не сработает :(
                                '''

                                if lesson_by_main_timetable in timetable_dict[num_lesson][ind][-3].lower():
                                    del timetable_dict[num_lesson][ind]

                        else:
                            """Все остальные случаи"""
                            new_lesson_info = [replace_for_lesson, [rep_name], rep_audience_array]

                            if last_num_lesson == num_lesson:
                                """Если номер в прошлой итерации равен текущему номеру пары"""
                                timetable_dict[num_lesson].append(new_lesson_info)

                            else:
                                timetable_dict[num_lesson][ind] = new_lesson_info

                            break

                    #last_name = rep_name

                else:
                    # бывают случаи, когда в основном расписании только одна пара, а в заменах "по расписанию"
                    # указаны 2 пары

                    # НУЖНО УЧЕСТЬ, ВОЗМОЖНОСТЬ НЕКОРРЕКТНОЙ РАБОТЫ МОДУЛЯ ОБРАБОТКИ "нет"
                    if replace_for_lesson.strip().lower() != 'нет':
                        """Если пара не отменяется, то добавляем её как новую"""
                        timetable_dict[num_lesson] = [[replace_for_lesson, [rep_name], rep_audience_array]]

                last_num_lesson = num_lesson

            self.filling_ready_timetable_data(date_, name_, timetable_dict)

    def filling_ready_timetable_data(self, date_, name_, timetable_dict):
        """Заполняем массив self.ready_timetable_data и кортеж lesson_names"""
        for num_lesson, lessons_array in timetable_dict.items():

            for one_lesson in lessons_array:
                lesson_name = one_lesson[0]
                teacher_name_array = one_lesson[1]
                audience_array = one_lesson[2]

                for teacher_name in teacher_name_array:
                    ind = teacher_name_array.index(teacher_name)

                    if len(audience_array) == 1:
                        ind = 0
                    audience = audience_array[ind]

                    data_one_lesson = (date_, name_, num_lesson, lesson_name, teacher_name, audience)

                    self.lesson_names.add(lesson_name)
                    self.ready_timetable_data.append(data_one_lesson)
