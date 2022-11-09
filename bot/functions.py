from aiogram import Dispatcher
from datetime import datetime, timedelta
import re
import requests
import time

from bot.parse import handler_parse     # import HandlerParse
from bot.config import ArrayTimes


def check_message_text(message, commands):
    return message.text.lower().replace('/', '') in commands


def check_callback_split(callback, commands: list, ind=-2):
    callback_data_split = callback.data.split()
    try:
        return callback_data_split[ind] in commands
    except Exception:
        return False


def no_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return

    return wrapper


def time_of_function(func):
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter_ns()
        res = func(*args, **kwargs)
        print(f"{func.__name__} {(time.perf_counter_ns() - start_time) / 10 ** 9}")
        return res

    return wrapped


def get_timezone_text(callback_data, interval=False):
    callback_data_split = re.split("[:|,]", str(callback_data))

    hours = int(callback_data_split[-3])
    minutes = int(callback_data_split[-2])

    if 'day' in callback_data_split[0]:
        hours -= 24
    timezone_text = f"{hours + 1 if minutes != 0 and hours < 0 else hours}:{minutes}{0 if minutes == 0 else ''}"

    if interval:
        timezone = timedelta(hours=hours, minutes=minutes)
        return timezone_text, timezone
    return timezone_text


def get_date_with_replaces(date_text: str, format_: str, replace_month=None, replace_year=None):
    try:
        date_ = datetime.strptime(date_text, format_).date()

        if replace_month is not None:
            date_ = date_.replace(month=replace_month)

        if replace_year is not None:
            date_ = date_.replace(year=replace_year)

        return date_
    except Exception:
        return


def get_correct_date(date_text: str, format_="%d.%m.%Y"):
    now_date = datetime.now().date()
    date_text_split = date_text.split('.')

    if len(date_text_split) == 1:
        return get_date_with_replaces(date_text, "%d", replace_month=now_date.month, replace_year=now_date.year)

    elif len(date_text_split) == 2:
        return get_date_with_replaces(date_text, "%d.%m", replace_year=now_date.year)

    year_text = date_text_split[-1]
    if len(year_text) == 2:
        format_ = "%d.%m.%y"

    return get_date_with_replaces(date_text, format_)


def get_next_check_time(func_name: str):
    """Расчет времени до следующего цикла в зависимости от имени функции"""
    delta = 0
    one_second = 0

    for t in get_call_later_time(func_name):
        now = datetime.now()

        one_second = round(now.microsecond / 1000000)

        check_t = datetime.strptime(t, "%H:%M")

        delta = timedelta(hours=now.hour - check_t.hour,
                          minutes=now.minute - check_t.minute,
                          seconds=now.second - check_t.second)

        seconds = delta.total_seconds()
        if seconds < 0:
            return seconds * (-1) + one_second

    seconds = (timedelta(hours=24) - delta).total_seconds()
    return seconds + one_second


def get_call_later_time(func_name: str):
    if func_name in ("update_matches", "live_notifications"):
        return ArrayTimes.update_matches

    elif func_name in ("update_news", "news_notifications"):
        return ArrayTimes.update_news

    elif func_name in ("update_events", ):
        return ArrayTimes.update_events

    return ("00:05, 23:55")


async def update_matches(dp: Dispatcher):
    """Обновляем данные через определённые интервалы времени для каждого типа обновления"""
    session = requests.Session()
    p = handler_parse.HandlerParse(session=session)
    p.upcoming_and_live()
    p.results()
    session.close()


async def update_news(dp: Dispatcher):
    session = requests.Session()
    p = handler_parse.HandlerParse(session=session)
    p.news()
    session.close()


async def update_events(dp: Dispatcher):
    session = requests.Session()
    p = handler_parse.HandlerParse(session=session)
    p.events()
    session.close()
