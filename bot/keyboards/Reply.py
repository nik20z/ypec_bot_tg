from aiogram.types import ReplyKeyboardMarkup


def default(row_width=2, resize_keyboard=True):
    """Дефолтная клавиатура"""
    keyboard = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize_keyboard)
    keyboard.row('Настройки', 'Расписание')
    return keyboard


def default_admin(row_width=2, resize_keyboard=True):
    """Дефолтная клавиатура для админа"""
    keyboard = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize_keyboard)
    keyboard.row('Настройки', 'Расписание', '/help_admin')
    return keyboard
