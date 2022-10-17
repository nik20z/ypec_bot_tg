from bot.database.connect import cursor, connection


def user(user_id: int):
    cursor.execute("DELETE FROM telegram WHERE user_id = {0}".format(user_id))
    connection.commit()


def ready_timetable_by_date(date_: str):
    cursor.execute("DELETE FROM ready_timetable WHERE date_ = '{0}'::date".format(date_))
    connection.commit()


def statistics(date_: str):
    cursor.execute("DELETE FROM stat WHERE date_ = '{0}'::date".format(date_))
    connection.commit()
