from bot.database.connect import cursor


def get_type_name_invert(type_name: str):
    """Получить инверсию типа профиля group_/teacher"""
    type_names = ['group_', 'teacher']
    return type_names[type_names.index(type_name) - 1]


def check_none(func):
    """Обработчик None-значений"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return None if not result else result[0]
    return wrapper


def concert_fetchall_to_list(result: tuple):
    """Конвертировать tuple to list"""
    return [x[0] for x in result]



def check_filling_table(table_name: str):
    """Проверка наличия данных в таблице True - если таблица пустая"""
    cursor.execute("SELECT EXISTS (SELECT * FROM {0})".format(table_name))
    return not cursor.fetchone()[0]


def view_main_timetable(type_name: str, name_: str, week_day_id=0, lesson_type=True):
    """Получить данные по основному расписанию в готовом виде"""
    type_name_invert = get_type_name_invert(type_name)

    query = """
            SELECT array_agg(DISTINCT num_lesson) AS num_les,
                   array_agg(DISTINCT lesson_name),
                   json_object_agg(DISTINCT COALESCE(NULLIF({1}_name, ''), '...'), audience_name),
                   array_agg(lesson_type)
            FROM main_timetable_info
            WHERE {0}_name = '{2}' AND week_day_id = {3} AND state_lesson AND (lesson_type ISNULL OR {4})
            GROUP BY num_lesson, {1}_name
            """.format(type_name,
                       type_name_invert,
                       name_,
                       week_day_id,
                       'lesson_type' if lesson_type else "True" if lesson_type is None else 'NOT lesson_type')
    cursor.execute(query)
    return cursor.fetchall()


def main_timetable(type_name: str, name_: str, week_day_id=0, lesson_type=True):
    """"""
    type_name_invert = get_type_name_invert(type_name)
    query = """
            SELECT num_lesson,
                   array_agg(DISTINCT lesson_name),
                   array_agg({1}_name),
                   array_agg(audience_name)
            FROM main_timetable_info
            WHERE {0}_name = '{2}' AND week_day_id = {3} AND state_lesson AND (lesson_type ISNULL OR {4})
            GROUP BY num_lesson, lesson_name
            """.format(type_name,
                       type_name_invert,
                       name_,
                       week_day_id,
                       'lesson_type' if lesson_type else "True" if lesson_type is None else 'NOT lesson_type')
    cursor.execute(query)
    return cursor.fetchall()


def replacement(type_name: str, name_: str):
    """Получить замены"""
    type_name_invert = get_type_name_invert(type_name)
    query = """
            SELECT num_lesson, 
                   array_agg(lesson_by_main_timetable), 
                   array_agg(DISTINCT replace_for_lesson), 
                   array_agg(DISTINCT {1}_name), 
                   array_agg(DISTINCT audience_name)
            FROM replacement_info
            WHERE {0}_name = '{2}'
            GROUP BY num_lesson, replace_for_lesson, teacher_name
            ORDER BY num_lesson, case when replace_for_lesson ILIKE '%расписан%' then 0 else 1 end
            """.format(type_name, type_name_invert, name_)
    cursor.execute(query)
    return cursor.fetchall()


def ready_timetable(type_name: str, date_: str, name_: str):
    """Получить готовое расписание"""
    reverse_type_name = {'group_': 'teacher', 'teacher': 'group_'}.get(type_name)
    query = """
            SELECT array_agg(DISTINCT num_lesson) AS num_les,
                   array_agg(DISTINCT COALESCE(NULLIF(lesson_name, ''), '...')),
                   json_object_agg(DISTINCT COALESCE(NULLIF({0}_name, ''), '...'), audience_name)
            FROM ready_timetable_info
            WHERE date_ = '{2}' AND {1}_name = '{3}'
            GROUP BY lesson_name, {0}_name
            ORDER BY num_les
            """.format(reverse_type_name, type_name, date_, name_)

    #  AND {0}_name IS NOT NULL

    cursor.execute(query)
    return cursor.fetchall()


def query_(query: str):
    """Выполнить произвольный запрос"""
    cursor.execute(query)
    return cursor.fetchall()


def query_info_by_name(table_name: str, info='id', default_method=False, value=None, similari_value=0.45):
    """Получить данные из конкретной таблицы по конкретному условию для lesson, audience, group_, teacher"""
    if default_method:
        query = """SELECT {0}_{1}
                    FROM {0}
                    WHERE {0}_name = %s""".format(table_name, info)
    else:
        query = """WITH similari AS (SELECT {0}_{1}, 
                                            similarity({0}_name, %s::varchar) AS similari_value
                                    FROM {0})
                    SELECT {0}_{1}
                    FROM similari
                    WHERE similari_value > {2}
                    ORDER BY similari_value DESC
                    LIMIT 1""".format(table_name, info, similari_value)
    if value is not None:
        cursor.execute(query, (value,))
        result = concert_fetchall_to_list(cursor.fetchall())
        return None if not result else result[0]

    return f"({query})"


def user_info(user_id: int):
    """Получить данные о пользователе"""
    query = """SELECT  CASE WHEN type_name THEN 'group_' ELSE 'teacher' END,
                        '',
                        name_id,
                        ARRAY(SELECT ARRAY[group__id::text, group__name, (group__id = ANY(spam_group__ids))::text]
                              FROM group_
                              WHERE ((type_name ISNULL) OR NOT(group__id = name_id AND type_name)) AND group__id = ANY(group__ids)) AS group__ids,
                        ARRAY(SELECT ARRAY[teacher_id::text, teacher_name, (teacher_id = ANY(spam_teacher_ids))::text]
                              FROM teacher
                              WHERE ((type_name ISNULL) OR NOT(teacher_id = name_id AND NOT type_name)) AND teacher_id = ANY(teacher_ids)) AS teacher_ids,
                        spamming, 
                        pin_msg, 
                        view_name, 
                        view_add, 
                        view_time
                FROM telegram
                WHERE user_id = {0}""".format(user_id)
    cursor.execute(query)
    return cursor.fetchone()


def user_info_by_colomn_names(user_id: int, colomn_names=None):
    """Данные о пользователе по конкретным колонкам"""
    if colomn_names is None:
        colomn_names = ['user_id']
    query = """SELECT {1}
                FROM telegram
                WHERE user_id = {0}""".format(user_id, ', '.join(colomn_names))
    cursor.execute(query)
    return cursor.fetchone()


def user_info_name_card(type_name: str, user_id: int, name_id: int):
    """Информация о подписках пользователя"""
    query = """SELECT {0}_name,
                        case 
                            when type_name
                            then {2} = name_id and '{0}' = 'group_'
                            else not type_name and {2} = name_id and '{0}' = 'teacher'
                        end,
                        {2} = ANY({0}_ids),
                        {2} = ANY(spam_{0}_ids)
                FROM telegram
                LEFT JOIN {0} ON {2} = {0}.{0}_id
                WHERE user_id = {1}""".format(type_name, user_id, name_id)
    cursor.execute(query)
    return cursor.fetchone()


def courses_and_group__name_array():
    """Вывести массивы групп по курсам"""
    query = """SELECT DISTINCT substring(group__name from 1 for 2) AS course_year,
                    array_agg(group__name ORDER BY group__name)
                FROM group_
                GROUP BY course_year
                ORDER BY course_year DESC"""
    cursor.execute(query)
    return cursor.fetchall()


def group_():
    query = """SELECT json_object_agg(group__id, 
                                      group__name ORDER BY group__name) 
                FROM group_ 
                GROUP BY substring(group__name from 1 for 2)"""
    cursor.execute(query)
    return cursor.fetchall()[::-1]


def all_info(table_name: str, colomn_name="group__name"):
    """Получить массив всех строчек по одной колонке"""
    query = """SELECT {1} FROM {0}""".format(table_name, colomn_name)
    cursor.execute(query)
    return concert_fetchall_to_list(cursor.fetchall())


def teacher(columns=['teacher_id', 'teacher_name']):
    """Получить информацию об учителях по колонкам"""
    query = "SELECT {0} FROM teacher ORDER BY teacher.teacher_name".format(', '.join(columns))
    cursor.execute(query)
    return cursor.fetchall()


@check_none
def value_by_id(table_name_: str, colomn_names: list, value: str, check_id_name_colomn: str):
    """Получить конкретный параметр: указывается Таблица, Название колонки, Значение, Название колонки"""
    query = "SELECT {1} FROM {0} WHERE {2} = %s".format(table_name_, ', '.join(colomn_names), check_id_name_colomn)
    cursor.execute(query, (value,))
    return cursor.fetchone()


@check_none
def config(value_: str):
    """Данные из таблицы config"""
    query = "SELECT value_ FROM config WHERE key_ = '{0}'".format(value_)
    cursor.execute(query)
    return cursor.fetchone()


def names_rep_different(type_name: str):
    """Получить id group_|teacher, расписание для которых различаются в таблицах replacement и replacement_temp"""
    type_name_invert = get_type_name_invert(type_name)
    query = """WITH rep_grouping AS (SELECT {0}_id, json_object_agg(num_lesson, 
                                                                    ARRAY[replace_for_lesson, 
                                                                          {1}_id::text, audience_id::text]
                                                                    ORDER BY num_lesson, 
                                                                            replace_for_lesson, 
                                                                            {1}_id, 
                                                                            audience_id)
                                     FROM replacement
                                     GROUP BY {0}_id),
                    rep_temp_grouping AS (SELECT {0}_id, json_object_agg(num_lesson, 
                                                                         ARRAY[replace_for_lesson, 
                                                                               {1}_id::text, audience_id::text]
                                                                         ORDER BY num_lesson, 
                                                                                  replace_for_lesson, 
                                                                                  {1}_id, 
                                                                                  audience_id)
                                          FROM replacement_temp
                                          GROUP BY {0}_id)
                SELECT rep_grouping.{0}_id
                FROM rep_grouping
                LEFT JOIN rep_temp_grouping ON rep_grouping.{0}_id = rep_temp_grouping.{0}_id
                WHERE rep_grouping::text != rep_temp_grouping::text""".format(type_name, type_name_invert)
    cursor.execute(query)
    return concert_fetchall_to_list(cursor.fetchall())


def user_ids_telegram_by(type_name: str, name_id: int):
    """Получить список пользователей, которые подписаны на рассылку"""
    query = """SELECT user_id, pin_msg, view_name, view_add, view_time 
               FROM telegram 
               WHERE {1} = ANY(spam_{0}_ids) AND spamming""".format(type_name, name_id)
    cursor.execute(query)
    return cursor.fetchall()


def dates_ready_timetable(month: str):
    """Список дат с готовым расписанием для определённого месяца"""
    query = """SELECT DISTINCT date_
               FROM ready_timetable
               WHERE to_char(date_, 'Mon') = %s
               ORDER BY date_ DESC"""
    cursor.execute(query, (month,))
    return concert_fetchall_to_list(cursor.fetchall())


def months_ready_timetable():
    """Список месяцев для которых имеется готовое расписание"""
    query = """SELECT DISTINCT to_char(date_, 'Mon')
               FROM ready_timetable"""
    cursor.execute(query)
    return concert_fetchall_to_list(cursor.fetchall())
