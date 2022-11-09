from aiogram.types import ReplyKeyboardMarkup
from bot.keyboards.util import Button


def default(row_width=3, resize_keyboard=True):
    """Default user keyboard"""
    keyboard = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize_keyboard)
    keyboard.add('Today', 'Tomorrow', 'Live')
    keyboard.add('Events', 'Results today')
    return keyboard


def location(row_width=2, resize_keyboard=True, send_location_button=False):
    """"""
    keyboard = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=resize_keyboard)
    keyboard.add(Button("Selection timezone 📋").reply())

    if send_location_button:
        keyboard.add(Button("Send location 🗺").reply(request_location=True))

    return keyboard
