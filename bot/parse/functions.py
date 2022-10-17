

def get_full_link_by_part(main_link: str, part_link: str):
    """Получить готовую ссылку"""
    return f"{main_link}/{part_link}"


def convert_timetable_to_dict(timetable: list):
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


def convert_lesson_name(lesson_name):
    """Форматирование названия пары"""
    # первая заглавная
    try:
        lesson_name = lesson_name[0].upper() + lesson_name[1:]
    except IndexError:
        pass

    if 'по расписанию' in lesson_name.lower():
        return lesson_name

    # исправляем неправильно поставленные запятые
    # lesson_name = lesson_name.replace(' ,', ', ')
    # lesson_name = ', '.join(lesson_name.split(','))

    # исправляем самые частые ошибки
    for key, val in {'.': ' ',
                     ',': '',
                     '(': ' (',
                     ')': ') ',
                     '\\': '/',
                     'п/з': ' п/з ',
                     'к/р': ' к/р ',
                     'к/п': ' к/п ',
                     'л/р': ' л/р ',
                     '1/2': ' 1/2 ',
                     'п/гр': 'п/г'
                     }.items():
        lesson_name = lesson_name.replace(key, val)

    # удалить дублирующиеся слова
    for s in ('п/з', 'к/р', 'л/р', '1/2'):
        while True:
            if lesson_name.count(s) > 1:
                ind = lesson_name.rfind(s)
                lesson_name = lesson_name[:ind - 1] + lesson_name[ind + len(s):]
            else:
                break

    # убираем дублирование
    lesson_name = ' '.join(lesson_name.split())

    # добавляем "гр"
    if '1/2' in lesson_name and ' гр' not in lesson_name:
        lesson_name = lesson_name.replace('1/2', '1/2 гр')

    return lesson_name.strip()


def get_correct_audience(audience: str):
    """Получить отформатированное название аудитории"""
    audience = ''.join([i for i in audience if i.isalnum() or i in ('-', '/')])

    if audience in ("nbsp", "''", ""):
        return None

    if audience.isdigit():
        if int(audience) >= 100 or len(audience) >= 3:
            return f"А-{audience}"
        elif 10 <= int(audience) <= 50:
            return f"Б-{audience}"

    return audience.title()
