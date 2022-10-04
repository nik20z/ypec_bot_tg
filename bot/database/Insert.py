from bot.database.connect import cursor, connection
from bot.database.Select import query_info_by_name


def get_list_tuples(a):
    return [(x,) for x in a if x is not None]


def main_timetable(data: list):
    query = """INSERT INTO main_timetable
                    (group__id, 
                    week_day_id, 
                    state_lesson, 
                    lesson_type, 
                    num_lesson, 
                    lesson_name_id, 
                    teacher_id, 
                    audience_id)
                VALUES ({0},%s,%s,%s,%s,{1},{2},{3})
                ON CONFLICT DO NOTHING""".format(query_info_by_name('group_', default_method=True),
                                                 query_info_by_name('lesson', default_method=True),
                                                 query_info_by_name('teacher'),
                                                 query_info_by_name('audience', default_method=True))
    cursor.executemany(query, data)
    connection.commit()


def replacement(data: list, table_name="replacement"):
    query = """INSERT INTO {0}
                    (group__id,
                     num_lesson,
                     lesson_by_main_timetable,
                     replace_for_lesson,
                     teacher_id,
                     audience_id)
                VALUES ({1},%s,%s,%s,{2},{3})
                """.format(table_name,
                           query_info_by_name('group_', default_method=True),
                           query_info_by_name('teacher'),
                           query_info_by_name('audience', default_method=True))
    cursor.executemany(query, data)
    connection.commit()


def ready_timetable(data: list):
    query = """INSERT INTO ready_timetable
                            (date_,
                             group__id,
                             num_lesson,
                             lesson_name_id,
                             teacher_id,
                             audience_id)
                        VALUES (%s,{0},%s,{1},{2},{3})
                        ON CONFLICT DO NOTHING""".format(query_info_by_name('group_', default_method=True),
                                                         query_info_by_name('lesson', default_method=True),
                                                         query_info_by_name('teacher'),
                                                         query_info_by_name('audience', default_method=True))
    cursor.executemany(query, data)
    connection.commit()


def group_(group__names: list):
    query = """INSERT INTO group_
                (group__name)
                VALUES (%s)
                ON CONFLICT (group__name) DO UPDATE
                SET group__name = EXCLUDED.group__name"""
    cursor.executemany(query, get_list_tuples(group__names))
    connection.commit()


def teacher(teacher_names: list):
    query = """INSERT INTO teacher
                (teacher_name)
                VALUES (%s)
                ON CONFLICT (teacher_name) DO UPDATE
                SET teacher_name = EXCLUDED.teacher_name"""
    cursor.executemany(query, get_list_tuples(teacher_names))
    connection.commit()


def lesson(lesson_names: list):
    query = """INSERT INTO lesson
                (lesson_name)
                VALUES (%s)
                ON CONFLICT (lesson_name) DO UPDATE
                SET lesson_name = EXCLUDED.lesson_name"""
    cursor.executemany(query, get_list_tuples(lesson_names))
    connection.commit()


def audience(audience_names: list):
    query = """INSERT INTO audience
                (audience_name)
                VALUES (%s)
                ON CONFLICT (audience_name) DO UPDATE
                SET audience_name = EXCLUDED.audience_name"""
    cursor.executemany(query, get_list_tuples(audience_names))
    connection.commit()


def new_user(data_: tuple):
    cursor.execute("INSERT INTO telegram (user_id, user_name, joined) VALUES (%s, %s, %s)", data_)
    connection.commit()


def config(key_: str, value_: str):
    query = """INSERT INTO config
                        (key_, value_)
                        VALUES (%s, %s)
                        ON CONFLICT (key_) DO UPDATE
                        SET value_ = EXCLUDED.value_
                        """
    cursor.execute(query, (key_, value_,))
    connection.commit()
