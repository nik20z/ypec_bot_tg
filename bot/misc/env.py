from os import environ
from typing import Final


class Keys:
    TG_TOKEN: Final = environ.get('TG_TOKEN', '2070598588:123456789')


class DataBase:
    SETTINGS: Final = environ.get('SETTINGS', {'user': "ypec",
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
    SBERBANK: Final = environ.get('SBERBANK', "https://www.sberbank.ru/ru/person/dl/123456789")
    YOOMONEY: Final = environ.get('YOOMONEY', "https://sobe.ru/na/B2W2x1U0o2L6")
    BOOSTY: Final = environ.get('BOOSTY', "https://boosty.to/ypec_bot")
    BITCOIN: Final = environ.get('BTC', "123456789")
    ETHERIUM: Final = environ.get('ETH', "123456789")


class Communicate:
    TG_BOT: Final = environ.get('TG_BOT', "https://t.me/ypec_bot")
    VK_BOT: Final = environ.get('VK_BOT', "https://vk.com/ypec_bot")
    DEVELOPER: Final = environ.get('DEVELOPER', "https://vk.com/id264311526")
    INSTAGRAM: Final = environ.get('INSTAGRAM', "https://www.instagram.com/your.oldfr1end")
    OFFICIAL_SITE: Final = environ.get('OFFICIAL_SITE', "https://www.ypec.ru/")
    OFFICIAL_VK_GROUP: Final = environ.get('OFFICIAL_VK_GROUP', "https://vk.com/ypecnews")
