from bot.database.connect import cursor, connection

from bot.database import Select


def get_list_tuples(a):
    return [(x,) for x in a if x is not None]


def main_timetable(data: list):
    query = """INSERT INTO main_timetable
                    (group__id, 
                    week_day_id,
                    lesson_type, 
                    num_lesson, 
                    lesson_name_id, 
                    teacher_id, 
                    audience_id)
                VALUES ({0},%s,%s,%s,{1},{2},{3})
                ON CONFLICT DO NOTHING""".format(Select.query_info_by_name('group_', default_method=True),
                                                 Select.query_info_by_name('lesson', default_method=True),
                                                 Select.query_info_by_name('teacher'),
                                                 Select.query_info_by_name('audience', default_method=True))
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
                           Select.query_info_by_name('group_', default_method=True),
                           Select.query_info_by_name('teacher'),
                           Select.query_info_by_name('audience', default_method=True))
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
                        ON CONFLICT DO NOTHING""".format(Select.query_info_by_name('group_', default_method=True),
                                                         Select.query_info_by_name('lesson', similari_value=0.8),
                                                         Select.query_info_by_name('teacher'),
                                                         Select.query_info_by_name('audience', default_method=True))
    cursor.executemany(query, data)
    connection.commit()


def group_(group__names: list):
    group_names_in_table = Select.all_info(table_name="group_", column_name="group__name")
    names_array = list(set(group__names) - set(group_names_in_table))

    query = """INSERT INTO group_
                (group__name)
                VALUES (%s)
                ON CONFLICT DO NOTHING"""
    cursor.executemany(query, get_list_tuples(names_array))
    connection.commit()


def teacher(teacher_names: list):
    teacher_names_in_table = Select.all_info(table_name="teacher", column_name="teacher_name")
    names_array = list(set(teacher_names) - set(teacher_names_in_table))

    query = """INSERT INTO teacher
                (teacher_name)
                VALUES (%s)
                ON CONFLICT DO NOTHING"""
    cursor.executemany(query, get_list_tuples(names_array))
    connection.commit()


def lesson(lesson_names: list):
    lesson_names_in_table = Select.all_info(table_name="lesson", column_name="lesson_name")
    names_array = list(set(lesson_names) - set(lesson_names_in_table))

    query = """INSERT INTO lesson
                (lesson_name)
                VALUES (%s)
                ON CONFLICT DO NOTHING"""
    cursor.executemany(query, get_list_tuples(names_array))
    connection.commit()


def audience(audience_names: list):
    audience_names_in_table = Select.all_info(table_name="audience", column_name="audience_name")
    names_array = list(set(audience_names) - set(audience_names_in_table))

    query = """INSERT INTO audience
                (audience_name)
                VALUES (%s)
                ON CONFLICT DO NOTHING"""
    cursor.executemany(query, get_list_tuples(names_array))
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
