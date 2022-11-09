from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup
from datetime import datetime, timedelta
import re

from bot.parse import Url


class Button:
    def __init__(self, text: str):
        self.text = str(text)

    def inline(self,
               callback_data: str,
               url=None):
        return InlineKeyboardButton(text=self.text,
                                    callback_data=str(callback_data),
                                    url=url)

    def reply(self, request_location=False):
        return KeyboardButton(text=self.text,
                              request_location=request_location)


def get_condition_smile(bool_value):
    return '✅' if bool_value else '☑'


def split_array(arr, n):
    a = []
    for i in range(0, len(arr), n):
        a.append(arr[i:i + n])
    return a


def get_close_button():
    return Button("❌").inline("close")


def get_paging_button(callback, direction="left"):
    return Button('⬅' if direction == "left" else '➡').inline(callback)


def add_in_text(text, added_text, side='right'):
    added_text = '' if added_text is None else added_text
    if side == 'left':
        return f"{added_text} {text}"
    elif side == 'right':
        return f"{text} {added_text}"
    return text


def format_date(date_):
    return datetime.strftime(date_, '%#d %b (%A)')


def get_timezone_text(callback_data, interval=False):
    callback_data_split = re.split(":|,", str(callback_data))

    hours = int(callback_data_split[-3])
    minutes = int(callback_data_split[-2])

    if 'day' in callback_data_split[0]:
        hours -= 24
    timezone_text = f"{hours + 1 if minutes != 0 and hours < 0 else hours}:{minutes}{0 if minutes == 0 else ''}"

    if interval:
        timezone = timedelta(hours=hours, minutes=minutes)
        return timezone_text, timezone
    return timezone_text


def get_smile_condition(parameter: bool):
    if parameter:
        return '✅'
    return '☑'


def get_match_button(match,
                     last_callback_data,
                     add_time=False,
                     add_live_mark=False,
                     add_url=False,
                     url=None,
                     add=False,
                     row_width=3):
    match_id = match[0]
    match_type = match[1]
    match_time = match[2]
    team1_name = match[3]
    team2_name = match[4]
    # event_id = match[5]
    event_name = match[6]
    result_score = match[7]

    short_time = match_type == 'R'
    button_text = ""

    if match_type == 'U':
        add_time = True
        button_text = f"{team1_name} vs {team2_name}"

    elif match_type == 'L':
        button_text = f"{'⭕ ' if add_live_mark else ''}{team1_name} vs {team2_name}"

    elif match_type == 'R':
        button_text = f"{team1_name} {result_score[0]} - {result_score[-1]} {team2_name}"

    if add_time and match_type != 'L':
        if short_time:
            match_time = ' '.join(match_time.split()[:2])
        button_text = f"{match_time} | {button_text}"

    match_callback_data = f"{last_callback_data} mi {match_id}"

    # если до этого открывали матчи для ивента и переходили под конкретную игры или открыли матчи из карточки команды
    if 'em mi' in match_callback_data and 'um' in match_callback_data:
        add_url = True

    if add_url:
        url = Url.match_or_analytics('M', match_id, team1_name, team2_name, event_name)

    button = Button(button_text).inline(match_callback_data, url=url)

    if add:
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(button)
        return keyboard
    return button


def get_team_button(obj, last_callback_data: str, add_flag=False):
    """"""
    team_id = obj[0]
    team_name = obj[1]
    flag = obj[2] if add_flag else None

    text_button = add_in_text(team_name, flag)
    callback_data = f"{last_callback_data} ti {team_id}"

    return Button(text_button).inline(callback_data)


def get_player_button(obj, last_callback_data: str, add_flag=True):
    player_id = obj[0]
    player_nik_name = obj[1]
    # player_name = obj[2]
    flag = obj[3] if add_flag else None

    text_button = add_in_text(player_nik_name, flag)
    callback_data = f"{last_callback_data} pi {player_id}"

    # Если до этого вызывали список игроков команды, то делаем кнопки-ссылки на игроков
    if last_callback_data.split().count('pt') > 1:
        url_player = Url.player(player_id, player_nik_name)
        return Button(text_button).inline(player_id, url=url_player)

    return Button(text_button).inline(callback_data)


def get_event_button(obj, last_callback_data):
    event_id = obj[0]
    event_name = obj[1]

    text_button = event_name
    callback_data = f"{last_callback_data} ei {event_id}"

    return Button(text_button).inline(callback_data)


def get_update_button(callback_data):
    return Button("🔄").inline(callback_data)


def get_subscribe_button(subscription, last_callback_data):
    subscription_to_notifications = f"notice {last_callback_data}"
    return Button('✅' if subscription else '➕').inline(subscription_to_notifications)


def get_back_button(last_callback_data,
                    return_keyboard=False,
                    offset=-2):
    """Кнопка возврата"""
    if offset is None:
        back_callback_data = last_callback_data
    else:
        back_callback_data = ' '.join(last_callback_data.split()[:offset])

    back_button = Button("🔙").inline(back_callback_data)  # 🔙⬅◀

    if return_keyboard:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(back_button)
        return keyboard

    return back_button
