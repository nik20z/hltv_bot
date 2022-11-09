from os import environ
from typing import Final


class TgKeys:
    TOKEN: Final = environ.get('TOKEN', '123456789')


class DataBase:
    SETTINGS: Final = environ.get('SETTINGS', {'user': "hltv",
                                               'password': "123456789",
                                               'host': "localhost",
                                               'port': 5432,
                                               'database': "hltv_bot"})


class Communicate:
    VK: Final = environ.get('VK', "https://vk.com/id264311526")
    INSTAGRAM: Final = environ.get('INSTAGRAM', "https://www.instagram.com/your.oldfr1end")
