from aiogram.types import CallbackQuery


def check_call(callback: CallbackQuery, commands: list, ind=-1):
    """Проверка вхождения команды в callback по индексу"""
    callback_data_split = callback.data.split()
    try:
        return callback_data_split[ind] in commands
    except IndexError:
        return False


def get_callback_values(callback: CallbackQuery, last_ind: int):
    """Получить callback_data_split и last_callback_data с ограничением по индексу"""
    callback_data_split = callback.data.split()
    last_callback_data = ' '.join(callback_data_split[:last_ind])
    return callback_data_split, last_callback_data


column_name_by_callback = {'sp_gr': 'spam_group_',
                           'sub_gr': 'group_',
                           'sp_tch': 'spam_teacher',
                           'sub_tch': 'teacher',
                           'm_sub_gr': 'group_',
                           'm_sub_tch': 'teacher',
                           'g_rt': 'group_',
                           'g_list': 'group_',
                           'gc': 'group_',
                           't_rt': 'teacher',
                           't_list': 'teacher',
                           'tc': 'teacher'
                           }
