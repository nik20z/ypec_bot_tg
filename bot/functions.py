from datetime import datetime, date, timedelta
import requests


def month_translate(month_name: str):
    """Перевести название месяца на русский язык"""
    month_d = {'jan': 'январь',
               'feb': 'февраль',
               'mar': 'март',
               'apr': 'апрель',
               'may': 'май',
               'june': 'июнь',
               'jun': 'июнь',
               'july': 'июль',
               'jul': 'июль',
               'aug': 'август',
               'sep': 'сентябрь',
               'oct': 'октябрь',
               'now': 'ноябрь',
               'dec': 'декабрь'
               }
    res = month_d.get(month_name.lower().strip())
    if res is not None:
        return res.title()


def week_day_translate(week_day_name: str):
    """Перевести название дня недели на русский язык"""
    week_day_d = {'monday': 'понедельник',
                  'mon': 'понедельник',
                  'tuesday': 'вторник',
                  'tue': 'вторник',
                  'tu': 'вторник',
                  'wednesday': 'среда',
                  'wed': 'среда',
                  'we': 'среда',
                  'thursday': 'четверг',
                  'thu': 'четверг',
                  'th': 'четверг',
                  'friday': 'пятница',
                  'fri': 'пятница',
                  'fr': 'пятница',
                  'saturday': 'суббота',
                  'sat': 'суббота',
                  'sa': 'суббота',
                  'sunday': 'воскресенье',
                  'sun': 'воскресенье',
                  'su': 'воскресенье'
                  }
    res = week_day_d.get(week_day_name.lower().strip())
    if res is not None:
        return res.title()


def get_week_day_name_by_id(wee_day_id: int, type_case="default", bold=True):
    """Получить название дня недели по id"""
    week_array = {'default': ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'],
                  'genitive': ['понедельника', 'вторника', 'среды', 'четверга', 'пятницы', 'субботы'],
                  'prepositional': ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу']}
    week_day_text = week_array[type_case][int(wee_day_id)].title()
    if bold:
        return f"<b>{week_day_text}</b>"
    return week_day_text


def get_day_text(date_=None, days=0, delete_sunday=True, format_str="%d.%m.%Y"):
    """Получить отформатированную дату"""
    if date_ is None:
        date_ = date.today()

    if delete_sunday and date_.weekday() == 5:
        days = 2

    return (date_ + timedelta(days=days)).strftime(format_str)


def get_week_day_id_by_date_(date_: str, format_str="%d.%m.%Y"):
    """Получить номер недели по дате"""
    return datetime.strptime(date_, format_str).weekday()


def get_rub_balance(login: str, api_access_token: str):
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
