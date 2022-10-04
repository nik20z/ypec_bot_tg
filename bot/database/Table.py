from bot.database.connect import cursor, connection

view_create_queries = {
    "main_timetable_info": """CREATE OR REPLACE VIEW main_timetable_info AS
                                    SELECT group__name, 
                                            week_day_id, 
                                            state_lesson, 
                                            num_lesson,
                                            lesson_type,
                                            lesson_name,
                                            teacher_name,
                                            audience_name
                                    FROM main_timetable
                                    LEFT JOIN group_ ON main_timetable.group__id = group_.group__id
                                    LEFT JOIN lesson ON main_timetable.lesson_name_id = lesson.lesson_id 
                                    LEFT JOIN teacher ON main_timetable.teacher_id = teacher.teacher_id 
                                    LEFT JOIN audience ON main_timetable.audience_id = audience.audience_id;""",

    "replacement_info": """CREATE OR REPLACE VIEW replacement_info AS
                                SELECT group__name,
                                        num_lesson,
                                        lesson_by_main_timetable,
                                        replace_for_lesson,
                                        teacher_name,
                                        audience_name
                                FROM replacement
                                LEFT JOIN group_ ON replacement.group__id = group_.group__id
                                LEFT JOIN teacher ON replacement.teacher_id = teacher.teacher_id 
                                LEFT JOIN audience ON replacement.audience_id = audience.audience_id;""",

    "ready_timetable_info": """CREATE OR REPLACE VIEW ready_timetable_info AS
                                    SELECT date_,
                                            group__name,
                                            num_lesson,
                                            lesson_name,
                                            teacher_name,
                                            audience_name
                                    FROM ready_timetable
                                    LEFT JOIN group_ ON ready_timetable.group__id = group_.group__id
                                    LEFT JOIN lesson ON ready_timetable.lesson_name_id = lesson.lesson_id 
                                    LEFT JOIN teacher ON ready_timetable.teacher_id = teacher.teacher_id 
                                    LEFT JOIN audience ON ready_timetable.audience_id = audience.audience_id"""
}

table_create_queries = {
    "group_": """CREATE TABLE IF NOT EXISTS group_ (
                                        group__id smallserial NOT NULL PRIMARY KEY,
                                        group__name varchar(10) NOT NULL UNIQUE);""",

    "teacher": """CREATE TABLE IF NOT EXISTS teacher (
                                        teacher_id smallserial NOT NULL PRIMARY KEY,
                                        teacher_name varchar(35) NOT NULL UNIQUE);""",

    "lesson": """CREATE TABLE IF NOT EXISTS lesson (
                                        lesson_id smallserial NOT NULL PRIMARY KEY,
                                        lesson_name text NOT NULL UNIQUE);""",

    "audience": """CREATE TABLE IF NOT EXISTS audience (
                                        audience_id smallserial NOT NULL PRIMARY KEY,
                                        audience_name text NOT NULL UNIQUE);""",

    "main_timetable": """CREATE TABLE IF NOT EXISTS main_timetable (
                                        group__id smallint REFERENCES group_ (group__id),
                                        week_day_id smallint,
                                        state_lesson boolean DEFAULT True,
                                        num_lesson varchar(10),
                                        lesson_type boolean,
                                        lesson_name_id smallint REFERENCES lesson (lesson_id),
                                        teacher_id smallint REFERENCES teacher (teacher_id),
                                        audience_id smallint REFERENCES audience (audience_id));""",

    "replacement": """CREATE TABLE IF NOT EXISTS replacement (
                                        group__id smallint REFERENCES group_ (group__id),
                                        num_lesson varchar(10),
                                        lesson_by_main_timetable text,
                                        replace_for_lesson text,
                                        teacher_id smallint REFERENCES teacher (teacher_id),
                                        audience_id smallint REFERENCES audience (audience_id));""",

    "replacement_temp": "CREATE TABLE IF NOT EXISTS replacement_temp (LIKE replacement INCLUDING ALL);",

    "ready_timetable": """CREATE TABLE IF NOT EXISTS ready_timetable (
                                        date_ date,
                                        group__id smallint REFERENCES group_ (group__id),
                                        num_lesson varchar(10),
                                        lesson_name_id smallint REFERENCES lesson (lesson_id),
                                        teacher_id smallint REFERENCES teacher (teacher_id),
                                        audience_id smallint REFERENCES audience (audience_id));""",

    "telegram": """CREATE TABLE IF NOT EXISTS telegram (
                                        user_id bigint NOT NULL PRIMARY KEY,
                                        user_name text,
                                        joined date,
                                        type_name boolean,
                                        name_id smallint,        									
                                        group__ids smallint[],
                                        teacher_ids smallint[],
                                        spam_group__ids smallint[],
                                        spam_teacher_ids smallint[],
                                        spamming boolean DEFAULT True,
                                        pin_msg boolean DEFAULT True, 
                                        view_name boolean DEFAULT True, 
                                        view_add boolean DEFAULT True, 
                                        view_time boolean DEFAULT False,
                                        ban boolean DEFAULT False,
                                        number_bans smallint DEFAULT 0,
                                        timeout_ban timestamp without time zone,
                                        bot_blocked boolean DEFAULT False
                                        );""",

    "config": """CREATE TABLE IF NOT EXISTS config (
                                        key_ text NOT NULL PRIMARY KEY,
                                        value_ text DEFAULT NULL);"""

}


def drop(table_name=None, cascade_state=False):
    if table_name is None:
        for table_name in table_create_queries.keys():
            drop(table_name)
    cascade = "CASCADE" if cascade_state else ""
    cursor.execute(f"DROP TABLE IF EXISTS {table_name} {cascade};")
    connection.commit()


def create(table_name=None):
    if table_name is None:
        for table_name in table_create_queries.keys():
            create(table_name=table_name)
    else:
        cursor.execute(table_create_queries.get(table_name, None))
        connection.commit()


def create_view(view_name=None):
    if view_name is None:
        for view_name in view_create_queries.keys():
            create_view(view_name=view_name)
    else:
        cursor.execute(view_create_queries.get(view_name, None))
        connection.commit()


def delete(table_name=None):
    if table_name is None:
        for table_name in table_create_queries.keys():
            delete(table_name)
    else:
        cursor.execute(f"DELETE FROM {table_name};")
        connection.commit()
