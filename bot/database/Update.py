from bot.database.connect import cursor, connection


def user_settings(user_id: int, key: str, value: str, convert_val_text: object = True):
    """Изменить параметр в настройках пользователя по названию колонки"""
    query = "UPDATE telegram SET {0} = {1} WHERE user_id = {2}".format(key, value, user_id)
    if convert_val_text:
        query = "UPDATE telegram SET {0} = '{1}' WHERE user_id = {2}".format(key, value, user_id)

    cursor.execute(query)
    connection.commit()


def user_settings_bool(user_id: int, name_: str):
    """Инверсия булевых значений в настройках пользователя"""
    query = """UPDATE telegram 
                SET {0} = NOT {0}
                WHERE user_id = {1}
                RETURNING {0}
                """.format(name_, user_id)
    cursor.execute(query)
    connection.commit()
    return cursor.fetchone()[0]


def user_settings_value(user_id: int, name_: str, value: str, remove_=False):
    """Занести в массив если не равно, иначе - удалить из массива"""
    if remove_:
        query = """UPDATE telegram 
                    SET {1} = NULL
                    WHERE user_id = {0} AND {1} = {2}
                    RETURNING True
                    """.format(user_id,
                               name_,
                               value)
    else:
        query = """UPDATE telegram 
                    SET {1} = case
                              when {1} = {2}
                              then NULL
                              else {2}
                              end 
                    WHERE user_id = {0}
                    RETURNING NOT {1} ISNULL
                    """.format(user_id,
                               name_,
                               value)
    cursor.execute(query)
    connection.commit()
    res = cursor.fetchone()
    return False if res is None else res[0]


def user_settings_array(user_id: int, name_: str, value: str, remove_=False, append_=False):
    """Занести в массив если не равно или удалить если равно
        Если remove is None, то не удалять, а только добавлять, если нет
        Если append is None, то не добавлять, а только удалять при наличии
    """
    if remove_:
        query = """UPDATE telegram
                    SET {1}_ids = array_remove({1}_ids, {2}::smallint)
                    WHERE user_id = {0}
                    RETURNING {2} = ANY({1}_ids)
                    """.format(user_id,
                               name_,
                               value)
    elif append_:
        query = """UPDATE telegram
                    SET {1}_ids = array_append({1}_ids, {2}::smallint)
                    WHERE user_id = {0}
                    RETURNING {2} = ANY({1}_ids)
                    """.format(user_id,
                               name_,
                               value)
    else:
        query = """UPDATE telegram
                    SET {1}_ids = CASE 
                        WHEN NOT {2} = ANY({1}_ids) OR {1}_ids ISNULL
                            THEN {4}
                        ELSE {3}
                        END
                    WHERE user_id = {0}
                    RETURNING {2} = ANY({1}_ids)
                    """.format(user_id,
                               name_,
                               value,
                               f"{name_}_ids" if remove_ is None else f"array_remove({name_}_ids, {value}::smallint)",
                               f"{name_}_ids" if append_ is None else f"array_append({name_}_ids, {value}::smallint)")
    cursor.execute(query)
    connection.commit()
    return cursor.fetchone()[0]


def change_id(table_name, colomn_name, id_, new_id):
    """Запрос на замену id предметов или аудиторий в таблице ready_timetable"""
    query = """UPDATE {0}
               SET {1}_id = {3}
               WHERE {1}_id = {2}""".format(table_name, colomn_name, id_, new_id)
    cursor.execute(query)
    connection.commit()
