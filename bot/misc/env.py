from os import environ
from typing import Final


class TgKeys:
    TOKEN: Final = environ.get('TOKEN', '2070598588:123456789')


class DataBase:
    SETTINGS: Final = environ.get('SETTINGS', {'user': "postgres",
                                               'password': "123456789",
                                               'host': "localhost",
                                               'port': 5432,
                                               'database': 'ypec_bot'})


class Qiwi:
    NUMBER_PHONE: Final = environ.get('NUMBER_PHONE', '123456789')
    TOKEN: Final = environ.get('TOKEN', '123456789')


class Donate:
    TINKOFF: Final = environ.get('TINKOFF', "https://www.tinkoff.ru/cf/123456789")
    QIWI: Final = environ.get('QIWI', "https://qiwi.com/p/123456789")
    SBERBANK: Final = environ.get('SBERBANK', "https://www.sberbank.ru/ru/person/dl/jc?linkname=123456789")


class Communicate:
    VK: Final = environ.get('VK', "https://vk.com/id264311526")
    INSTAGRAM: Final = environ.get('INSTAGRAM', "https://www.instagram.com/your.oldfr1end")
