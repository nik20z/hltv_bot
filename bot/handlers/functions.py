from datetime import datetime

from bot.parse import Url


def check_call(call, commands: list, ind=-2):
    callback_data_split = call.data.split()
    try:
        return callback_data_split[ind] in commands
    except Exception:
        return False


def check_message_text(message, commands):
    return message.text.lower().replace('/', '') in commands


def get_date_with_replaces(date_text: str, format_: str, replace_month=None, replace_year=None):
    try:
        date_ = datetime.strptime(date_text, format_).date()

        if replace_month is not None:
            date_ = date_.replace(month=replace_month)

        if replace_year is not None:
            date_ = date_.replace(year=replace_year)

        return date_
    except Exception:
        pass


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


def get_news_message(news_object, answer_text=''):
    for one_news in news_object:
        id_ = one_news[0]
        text = one_news[1]
        flag = one_news[2]
        href = one_news[3]

        url = Url.news(id_, href)

        answer_text += f"{flag} <a href='{url}'>{text}</a>\n\n"

    if answer_text == '':
        return False

    return answer_text
