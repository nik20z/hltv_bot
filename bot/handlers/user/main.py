import asyncio
from aiogram import Dispatcher
# from aiogram import types
from aiogram.types import Message, CallbackQuery

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

# from aiogram.utils.exceptions import TerminatedByOtherGetUpdates, BotBlocked
# from aiogram.utils.exceptions import MessageTextIsEmpty
from aiogram.utils.exceptions import MessageNotModified

import aiogram.utils.markdown as fmt

from datetime import datetime, timedelta
from loguru import logger
import random
from timezonefinder import TimezoneFinder
import pytz
import re

from bot.database import Select
from bot.database import Insert
from bot.database import Update

from bot.config import AnswerText
from bot.config import AnswerCallback
from bot.config import Info_Buttons_Description
from bot.config import ADMINS
from bot.config import notifications_limits

from bot.functions import get_timezone_text

from bot.keyboards import Inline
from bot.keyboards import Reply

from bot.handlers.functions import check_call
from bot.handlers.functions import check_message_text
from bot.handlers.functions import get_correct_date
from bot.handlers.functions import get_news_message

from bot.throttling import rate_limit


class UserStates(StatesGroup):
    """Класс состояний пользователя"""
    timezone_method = State()
    timezone = State()


async def message_from_blocked_user(message: Message):
    pass


async def new_user(message: Message, state: FSMContext):
    """Обработчик для нового пользователя"""
    user_id = message.chat.id
    joined = message.date
    language = message['from']['language_code']

    send_location_button = False

    if user_id > 0:
        user_name = message.chat.first_name
        user_name_quote = fmt.quote_html(user_name)
        text = AnswerText.new_user["welcome_message_private"](user_name_quote)
        send_location_button = True
    else:
        user_name = message.chat.title
        user_name_quote = fmt.quote_html(user_name)
        text = AnswerText.new_user["welcome_message_group"](user_name_quote)

    new_user_data = (user_id, language, user_name, joined)
    Insert.new_user(new_user_data)

    await state.update_data(send_help_message=True)
    await change_timezone(message, text=text, send_location_button=send_location_button)


async def change_timezone(message: Message, text=None, send_location_button=False):
    """"""
    chat_type = message.chat.type
    if text is None:
        if chat_type == 'private':
            text = AnswerText.change_timezone_private
            send_location_button = True
        elif chat_type == 'group':
            text = AnswerText.change_timezone_group

    keyboard = Reply.location(send_location_button=send_location_button)

    await message.answer(text, reply_markup=keyboard)
    await UserStates.timezone_method.set()


async def selection_timezone(message: Message):
    """"""
    text = AnswerText.selection_timezone
    keyboard = Inline.timezones()

    await message.answer(text, reply_markup=keyboard)
    await UserStates.timezone.set()


async def location(message: Message, state: FSMContext):
    user_id = message.chat.id

    await message.answer_chat_action('find_location')
    await asyncio.sleep(1)

    location = TimezoneFinder().timezone_at(lng=message.location.longitude, lat=message.location.latitude)
    user_timezone = datetime.now(pytz.timezone(location)).utcoffset()
    timezone_text = get_timezone_text(user_timezone)

    text = AnswerText.location(location, timezone_text)
    keyboard = Reply.default()

    await message.answer(text, reply_markup=keyboard)
    await state.finish()

    Update.user_timezone(user_id, user_timezone)


async def timezone(callback: CallbackQuery, state: FSMContext):
    [timezone_text, user_timezone] = get_timezone_text(callback.data, interval=True)

    # удаляем сообщение только в приватном чате
    if callback.message.chat.type == 'private':
        await callback.message.delete()
    else:
        await callback.message.edit_text(callback.message.text, reply_markup=None)

    text = AnswerText.timezone(timezone_text)
    keyboard = Reply.default()

    Update.user_timezone(callback.message.chat.id, user_timezone)

    await callback.message.answer(text, reply_markup=keyboard)
    user_state_data = await state.get_data()
    await state.finish()

    if "send_help_message" in user_state_data:
        await asyncio.sleep(2)
        await help_message(callback.message)


async def error_location_selection_message(message: Message):
    await message.answer(AnswerText.error_location_selection)


async def error_location_selection_callback(callback: CallbackQuery):
    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerText.error_location_selection)


async def error_location_send(message: Message):
    await message.answer(AnswerText.error_location_send)


async def error_location_send_callback(callback: CallbackQuery):
    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=AnswerText.error_location_send)


async def notice(callback: CallbackQuery):
    callback_data_split = callback.data.split()

    user_id = callback.message.chat.id
    type_notice = {'mi': 'matches', 'ei': 'events', 'ti': 'teams'}.get(callback_data_split[-2], False)
    id_ = callback_data_split[-1]

    if not type_notice:
        return

    limit = notifications_limits(type_notice)

    update_result, limit_condition = Update.user_notice(user_id, type_notice, id_, limit=limit)

    if limit_condition:
        text = AnswerCallback.notice_limit(type_notice, limit)
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)
    elif update_result:
        text = AnswerCallback.notice_by_type(type_notice)
    else:
        text = AnswerCallback.notice_deleted

    await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    if type_notice == 'matches':
        await match_info(callback)

    elif type_notice == 'events':
        await event_info(callback)

    elif type_notice == 'teams':
        await team_info(callback)


async def live_matches(message: Message, callback=None):
    """"""
    matches_array = Select.live_matches()

    date_ = datetime.today().date()
    last_callback_data = f"d L m {date_}"

    text = AnswerText.live_matches
    if not len(matches_array):
        text = AnswerText.no_live_matches
    keyboard = Inline.matches(matches_array, last_callback_data)

    if callback is None:
        return await message.answer(text, reply_markup=keyboard)

    # if not matches_array:
    # return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_live_broadcasts'])
    try:
        await message.edit_text(text, reply_markup=keyboard)
        await callback.bot.answer_callback_query(callback.id)
    except:
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.no_live_broadcasts)

    # await bot.answer_callback_query(callback.id)


async def dates_by_match_type(message: Message,
                              callback=None,
                              match_type=None,
                              text=None,
                              edit_message=False):
    """"""
    user_id = message.chat.id
    [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])

    # если нет информации о типе матча
    if match_type is None:
        match_type = 'U' if '/matches' in message.text else 'R'

    dates_array_sorted = Select.dates(user_timezone, match_type)

    if not len(dates_array_sorted) and edit_message:
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.no_dates)

    if text is None:
        text = AnswerText.dates_text_by_match_type(match_type)
    keyboard = Inline.dates(match_type, dates_array_sorted)

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
        return await callback.bot.answer_callback_query(callback.id)

    await message.answer(text, reply_markup=keyboard)


async def dates(callback: CallbackQuery,
                match_type=None,
                text=None,
                edit_message=True):
    if isinstance(callback, CallbackQuery):
        message = callback.message
        match_type = callback.data.split()[1]
    else:
        message = callback
        edit_message = False

    try:
        await dates_by_match_type(message,
                                  match_type=match_type,
                                  text=text,
                                  edit_message=edit_message, callback=callback)
    except MessageNotModified:
        answer_text = AnswerText.no_matches_by_type(match_type)
        await callback.bot.answer_callback_query(callback_query_id=callback.id, text=answer_text)


async def matches_or_results(message: Message):
    """"""
    print("matches_or_results")
    user_id = message.chat.id

    match_type = 'U' if check_message_text(message, ['today', 'tomorrow']) else 'R'
    [user_timezone, stars_matches_display] = Select.user_data_by_colomn_names(user_id,
                                                                              ['timezone_, stars_matches_display'])
    date_ = (datetime.utcnow() + user_timezone).date()

    if check_message_text(message, ['tomorrow']):
        date_ += timedelta(days=1)
    elif check_message_text(message, ['results yesterday', 'results_yesterday']):
        date_ += timedelta(days=-1)

    await matches_by_date(message,
                          match_type=match_type,
                          date_=date_,
                          user_timezone=user_timezone,
                          stars_matches_display=stars_matches_display)


async def matches_by_user_date(message: Message):
    user_id = message.chat.id

    command_split = message.text.split()
    match_type = {'matches': 'U'}.get(command_split[0].lower(), 'R')

    [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])

    date_text = command_split[-1].replace('/', '.').replace('-', '.')
    date_ = get_correct_date(date_text)

    if date_ is None:
        return await message.answer(AnswerText.correct_date)

    return await matches_by_date(message,
                                 match_type=match_type,
                                 date_=date_,
                                 user_timezone=user_timezone)


async def matches_by_date(callback,
                          match_type=None,
                          date_=None,
                          user_timezone=None,
                          stars_matches_display=0):
    """"""
    print("matches_by_date")
    if isinstance(callback, CallbackQuery):
        last_callback_data = callback.data
        callback_data_split = callback.data.split()

        match_type = callback_data_split[1]

        if match_type == 'L':
            return await live_matches(callback.message, callback=callback)

        date_text = callback_data_split[3]
        date_ = datetime.strptime(date_text, "%Y-%m-%d").date()

        user_id = callback.message.chat.id
        [user_timezone, stars_matches_display] = Select.user_data_by_colomn_names(user_id,
                                                                                  ['timezone_', 'stars_matches_display'])
    else:
        user_id = callback.chat.id
        last_callback_data = f"d {match_type} m {date_}"
        [stars_matches_display] = Select.user_data_by_colomn_names(user_id, ['stars_matches_display'])

    matches_array = Select.matches(match_type, date_, user_timezone, stars_matches_display)
    print("matches_array", matches_array)

    if not matches_array:
        answer_text = AnswerText.no_matches_by_type(match_type)
        return await dates(callback, match_type=match_type, text=answer_text)

    answer_text = AnswerText.matches_by_type(match_type) + AnswerText.filter_info({'stars': stars_matches_display})
    keyboard = Inline.matches(matches_array, last_callback_data, date_=date_)

    if isinstance(callback, Message):
        await callback.bot.send_message(chat_id=callback.chat.id, text=answer_text, reply_markup=keyboard)
    else:
        try:
            await callback.message.edit_text(answer_text, reply_markup=keyboard)
            await callback.bot.answer_callback_query(callback.id)
        except MessageNotModified:
            await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                     text=AnswerCallback.no_information_matches(match_type))


async def matches_by_team_id(callback: CallbackQuery):
    user_id = callback.message.chat.id

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()
    match_type = {'um': 'U', 'rm': 'R'}.get(callback_data_split[-2], 'U')
    team_id = callback_data_split[-1]

    [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])
    matches_array = Select.matches_by_team_id(team_id, match_type, user_timezone)

    if not len(matches_array):
        text = AnswerText.no_matches_by_type(match_type)
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = AnswerText.matches_by_team(match_type)
    keyboard = Inline.matches_by_team_id(matches_array, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def match_info(callback: CallbackQuery):
    user_id = callback.message.chat.id

    last_callback_data = callback.data.replace('notice ', '')
    match_id = int(last_callback_data.split()[-1])

    [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])
    subscription = Select.notice('matches', user_id, match_id)
    match_info_obj = Select.match_info(match_id, user_timezone)

    text = AnswerText.match_info
    keyboard = Inline.match_info(match_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


# @dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ti']))
async def team_info(callback: CallbackQuery):
    user_id = callback.message.chat.id

    last_callback_data = callback.data.replace('notice ', '')
    team_id = last_callback_data.split()[-1]

    if team_id == 'None':
        text = AnswerCallback.no_team_data
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    subscription = Select.notice('teams', user_id, team_id)
    team_info_obj = Select.team_info(team_id)

    text = AnswerText.team_info
    keyboard = Inline.team_info(team_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def details_by_team(callback: CallbackQuery):
    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    team_id = callback_data_split[-1]

    details_info = Select.details_by_team_id(team_id)

    text = AnswerText.details_by_team
    keyboard = Inline.details_by_team(details_info, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def players_by_team(callback: CallbackQuery):
    """"""
    print('players_by_team')
    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    team_id = callback_data_split[-1]

    players_info = Select.players_by_team_id(team_id)

    if not players_info:
        text = AnswerCallback.no_players_by_team
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = AnswerText.players_by_team
    keyboard = Inline.players_by_team(players_info, last_callback_data, add_flag=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def player_info(callback: CallbackQuery):
    #user_id = callback.message.chat.id

    last_callback_data = callback.data  # .replace('notice ', '')
    player_id = last_callback_data.split()[-1]

    if player_id == 'None':
        text = AnswerCallback.no_player_data
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    # subscription = SELECT.notice('players', user_id, player_id)
    player_info_obj = Select.player_info_by_id(int(player_id))

    text = AnswerText.player_info
    keyboard = Inline.player_info(player_info_obj, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def events(message: Message, callback=None, edit_message=False):
    if callback is None:
        message_text_split = message.text.split()
    else:
        message_text_split = callback.data.split()

    if len(message_text_split) == 1:
        text, keyboard = events_type()
    else:
        text, keyboard = events_by_date(message_text_split)

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
        return await callback.bot.answer_callback_query(callback.id)

    await message.answer(text, reply_markup=keyboard)


def events_type():
    text = AnswerText.events_type
    keyboard = Inline.events_type()  # row_width=1
    return text, keyboard


def get_event_date(date_text, format_="%m.%Y"):
    try:
        if len(date_text.split('.')) == 1:
            date_text = f"{date_text}.{datetime.now().year}"
        return date_text, datetime.strptime(date_text, format_).date()
    except:
        return date_text, None


def events_by_date(message_text_split, keyboard=None):
    date_text = message_text_split[-1].replace('/', '.').replace('-', '.')

    date_text, date_ = get_event_date(date_text)

    if date_ is None:
        text = AnswerText.correct_date_events
        return text, keyboard

    events_array = Select.events_by_date(date_text)

    if not len(events_array):
        text = AnswerText.no_events_by_date
        return text, keyboard

    last_callback_data = f"ebd {date_text}"

    date_text = datetime.strftime(date_, "%B %Y")
    text = AnswerText.events_by_date(date_text)
    keyboard = Inline.events_by_date(events_array, last_callback_data)

    return text, keyboard


async def events_by_date_edit(callback: CallbackQuery):
    await events(callback.message,
                 callback=callback,
                 edit_message=True)


async def events_type_edit(callback: CallbackQuery):
    text, keyboard = events_type()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def events_by_type(callback: CallbackQuery):
    last_callback_data = callback.data
    event_type = last_callback_data.split()[-1]

    events_array = Select.events_by_type(event_type)

    if not len(events_array):
        text = AnswerCallback.no_events_by_type(event_type)
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = AnswerText.text_by_event_type(event_type)
    # row_width=1
    keyboard = Inline.events(event_type, events_array, last_callback_data, add_months=event_type != 'O')

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def events_by_team(callback: CallbackQuery):
    last_callback_data = callback.data
    team_id = last_callback_data.split()[-1]

    events_array = Select.events_by_team(team_id)

    if not len(events_array):
        text = AnswerCallback.no_events_by_team
        return await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = AnswerText.events_by_team
    # row_width=1
    keyboard = Inline.events_by_team(events_array, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def event_info(callback: CallbackQuery):
    last_callback_data = callback.data.replace('notice ', '')
    event_id = last_callback_data.split()[-1]

    if event_id == 'None':
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.no_event_data)

    user_id = callback.message.chat.id
    subscription = Select.notice('events', user_id, event_id)

    event_info_obj = Select.event_info(event_id)

    text = AnswerText.event_info
    keyboard = Inline.event_info(event_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def event_matches(callback: CallbackQuery):
    user_id = callback.message.chat.id

    last_callback_data = callback.data
    event_id = int(last_callback_data.split()[-2])

    [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])
    matches_by_event_id_array = Select.matches_by_event_id(event_id, user_timezone)

    if not len(matches_by_event_id_array):
        return await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                                        text=AnswerCallback.no_event_matches)

    text = AnswerText.matches_for_event
    keyboard = Inline.matches(matches_by_event_id_array,
                              last_callback_data,
                              add_live_mark=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.bot.answer_callback_query(callback.id)


async def news(message: Message, callback=None, date_=None, date_for_message=''):
    news_object = Select.news(date_=date_)

    text = get_news_message(news_object, answer_text=date_for_message)

    if not len(news_object):
        await message.answer(AnswerText.no_news)

    elif callback is not None:
        try:
            keyboard = Inline.news()
            await message.edit_text(text,
                                    reply_markup=keyboard,
                                    disable_web_page_preview=True)
        except MessageNotModified:
            text = AnswerCallback.no_new_news
            await callback.bot.answer_callback_query(callback_query_id=callback.id, text=text)
    else:
        update_button = date_ is None  # нет необходимости обновлять новости о прошедших днях
        keyboard = Inline.news(update_button=update_button)
        await message.answer(text,
                             reply_markup=keyboard,
                             disable_web_page_preview=True)


async def news_by_date(message: Message):
    date_text = message.text.split()[-1].replace('/', '.').replace('-', '.')
    date_ = get_correct_date(date_text)

    if date_ is None:
        text = AnswerText.correct_date
        return await message.answer(text)

    date_for_message = f"<code>{datetime.strftime(date_, '%d %B %Y')}</code>\n\n"

    await news(message, date_=date_, date_for_message=date_for_message)


async def news_update(callback: CallbackQuery):
    await news(callback.message, callback=callback)


async def look_info(callback: CallbackQuery):
    answer_text = callback.data.replace('look_info ', '')

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=answer_text,
                                             show_alert=True)


async def settings(message: Message, edit=False):
    user_settings_info = Select.user_settings(message.chat.id)

    text = AnswerText.settings
    keyboard = Inline.settings(user_settings_info)

    if edit:
        return await message.edit_text(text, reply_markup=keyboard)
    await message.answer(text, reply_markup=keyboard)


async def settings_edit(callback: CallbackQuery):
    await settings(callback.message, edit=True)
    await callback.bot.answer_callback_query(callback.id)


async def info_button(callback: CallbackQuery):
    info_parameter = callback.data.split()[-1]
    text = Info_Buttons_Description.get(info_parameter, "No information")

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=text,
                                             show_alert=True)


async def settings_change(callback: CallbackQuery):
    user_id = callback.message.chat.id
    variable_parameter = callback.data.split()[-1]

    if variable_parameter == 'timezone':
        await callback.message.delete()
        return await change_timezone(callback.message)

    elif variable_parameter in ['receive_notices', 'news_notice', 'delete_old_matches', 'delete_old_events']:
        Update.user_bool_parameter(user_id, variable_parameter)
        await settings(callback.message, edit=True)

    elif variable_parameter == 'stars_matches_display':
        Update.stars_matches_display(user_id)
        await settings(callback.message, edit=True)

    await callback.bot.answer_callback_query(callback.id)


async def notice_info(callback: CallbackQuery):
    type_notice = callback.data.split()[-1]
    text = AnswerCallback.notice_info_by_type(type_notice)

    await callback.bot.answer_callback_query(callback_query_id=callback.id,
                                             text=text,
                                             show_alert=True)


async def notifications(message: Message,
                        edit=False,
                        last_callback_data='n',
                        add_back_button=False):
    user_id = message.chat.id

    all_notice_obj = Select.all_notice(user_id)

    print("all_notice_obj", all_notice_obj)

    d = {'teams': [], 'matches': [], 'events': []}
    for i in (0, 2, 4):
        notice_type = all_notice_obj[i]
        ids_array = all_notice_obj[i + 1]

        if ids_array is None or not ids_array:
            continue

        ids_array_sorted = sorted(ids_array)

        if notice_type == 'teams':
            d[notice_type] = Select.teams_by_ids_array(ids_array_sorted)

        elif notice_type == 'matches':
            [user_timezone] = Select.user_data_by_colomn_names(user_id, ['timezone_'])
            d[notice_type] = Select.matches_by_ids_array(ids_array_sorted, user_timezone)

        elif notice_type == 'events':
            d[notice_type] = Select.events_by_ids_array(ids_array_sorted)

    text = AnswerText.notifications
    keyboard = Inline.notifications(d, last_callback_data, add_team_flag=True)

    if edit:
        return await message.edit_text(text, reply_markup=keyboard)
    await message.answer(text, reply_markup=keyboard)


async def notifications_returned(callback: CallbackQuery):
    last_callback_data = callback.data
    await notifications(callback.message,
                        last_callback_data=last_callback_data,
                        edit=True)


async def search(message: Message,
                 callback=None,
                 type_search_short=None,
                 name_search=None,
                 edit=False):
    if name_search is None:
        message_text_lower = message.text.lower()
        try:
            type_search = message_text_lower.split()[1]
        except:
            type_search = None
        name_search = message.text.lower().replace(f"search {type_search} ", '')
        type_search_short = {'team': 't', 'player': 'p'}.get(type_search, None)

    if type_search_short is None:
        text = AnswerText.search_type_correct
        return await message.answer(text)

    if len(name_search) < 2 or not re.match("^[A-Za-z0-9-.']*$", name_search):
        text = AnswerText.search_enter_correct(type_search)
        return await message.answer(text)

    if type_search_short == 't':
        all_coincidences = Select.teams_by_name(name_search)
    elif type_search_short == 'p':
        all_coincidences = Select.player_id_by_name(name_search)

    if not len(all_coincidences):
        text = AnswerText.search_not_found(type_search)
        return await message.answer(text)

    last_callback_data = f"sch {type_search_short} {name_search}"

    text = AnswerText.search_results(name_search)

    if type_search_short == 't':
        keyboard = Inline.teams_list(all_coincidences, last_callback_data, add_flag=True)
    elif type_search_short == 'p':
        keyboard = Inline.players_list(all_coincidences, last_callback_data, return_keyboard=True, add_flag=True)

    if edit and callback is not None:
        await callback.message.edit_text(text, reply_markup=keyboard)
        return await callback.bot.answer_callback_query(callback.id)

    await message.answer(text, reply_markup=keyboard)


async def search_edit(callback: CallbackQuery):
    callback_data_split = callback.data.split()
    type_search_short = callback_data_split[1]
    name_search = callback_data_split[2]
    await search(callback.message,
                 callback=callback,
                 type_search_short=type_search_short,
                 name_search=name_search,
                 edit=True)


@rate_limit(1)
async def show_keyboard(message: Message):
    """Показать клавиатуру"""
    user_id = message.chat.id

    text = AnswerText.show_keyboard
    keyboard = Reply.default()
    # if user_id in ADMINS:
    #    keyboard = Reply.default_admin()

    await message.answer(text=text, reply_markup=keyboard)
    logger.info(f"message {user_id}")


# NOT CLICKABLE
async def button_not_clickable(callback: CallbackQuery):
    print(callback.data)
    # await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK["button_not_clickable"])
    # CreateLog(callback, 'button_not_clickable')
    await callback.message.delete()


async def close(callback: CallbackQuery):
    await callback.message.delete()


@rate_limit(1)
async def help_message(message: Message):
    """Вывести help-сообщение"""
    user_id = message.chat.id
    await message.answer(AnswerText.help)
    logger.info(f"message {user_id}")


@rate_limit(1)
async def other_messages(message: Message):
    """Обработчик сторонних сообщений"""
    user_id = message.chat.id
    text = random.choice(AnswerText.other_messages)

    await message.answer(text=text)
    logger.info(f"message {user_id}")


'''
async def bot_blocked(update: types.Update, exception: BotBlocked):
    pass
'''

'''
async def terminated_by_other_get_updates(update: types.Update, exception: TerminatedByOtherGetUpdates):
    await bot.send_message(chat_id=1020624735, text="Запущено 2 экземпляра бота")
'''

'''
MessageTextIsEmpty
'''


def register_user_handlers(dp: Dispatcher):
    # todo: register all user handlers

    dp.register_message_handler(new_user,
                                lambda msg: Select.user_info(user_id=msg.chat.id) is None,
                                content_types=['text'])

    dp.register_message_handler(change_timezone,
                                commands=['start', 'change_timezone'])

    dp.register_message_handler(selection_timezone,
                                Text(contains='selection timezone', ignore_case=True),
                                state=UserStates.timezone_method)

    dp.register_message_handler(location,
                                content_types=['location'],
                                state='*')

    dp.register_callback_query_handler(timezone,
                                       Text(contains=[':00']),
                                       state=UserStates.timezone)

    dp.register_message_handler(error_location_selection_message,
                                state=UserStates.timezone_method)

    dp.register_callback_query_handler(error_location_selection_callback,
                                       state=UserStates.timezone_method)

    dp.register_message_handler(error_location_send,
                                state=UserStates.timezone)

    dp.register_callback_query_handler(error_location_send_callback,
                                       state=UserStates.timezone)

    dp.register_callback_query_handler(notice,
                                       lambda call: check_call(call, ['notice'], ind=0))

    dp.register_message_handler(live_matches,
                                lambda msg: check_message_text(msg, ['live']))

    dp.register_message_handler(dates_by_match_type,
                                commands=['matches', 'results'])

    dp.register_callback_query_handler(dates,
                                       lambda call: check_call(call, ['d']))

    dp.register_message_handler(matches_or_results,
                                lambda msg: check_message_text(msg, ['today',
                                                                     'tomorrow',
                                                                     'results today',
                                                                     'results_today',
                                                                     'results yesterday',
                                                                     'results_yesterday'])
                                )

    dp.register_message_handler(matches_by_user_date,
                                Text(startswith=['matches', 'results'],
                                     ignore_case=True))

    dp.register_callback_query_handler(matches_by_date,
                                       lambda call: check_call(call, ['m']))

    dp.register_callback_query_handler(matches_by_team_id,
                                       lambda call: check_call(call, ['um', 'rm']))

    dp.register_callback_query_handler(match_info,
                                       lambda call: check_call(call, ['mi']))

    dp.register_callback_query_handler(team_info,
                                       lambda call: check_call(call, ['ti']))

    dp.register_callback_query_handler(details_by_team,
                                       lambda call: check_call(call, ['dt']))

    dp.register_callback_query_handler(players_by_team,
                                       lambda call: check_call(call, ['pt']))

    dp.register_callback_query_handler(player_info,
                                       lambda call: check_call(call, ['pi']))

    dp.register_message_handler(events,
                                lambda msg: check_message_text(msg, ['events']))

    dp.register_callback_query_handler(events_by_date_edit,
                                       lambda call: check_call(call, ['ebd']))

    dp.register_callback_query_handler(events_type_edit,
                                       lambda call: check_call(call, ['et'], ind=-1))

    dp.register_callback_query_handler(events_by_type,
                                       lambda call: check_call(call, ['ebt']))

    dp.register_callback_query_handler(events_by_team,
                                       lambda call: check_call(call, ['etm']))

    dp.register_callback_query_handler(event_info,
                                       lambda call: check_call(call, ['ei']))

    dp.register_callback_query_handler(event_matches,
                                       lambda call: check_call(call, ['em'], ind=-1))

    dp.register_message_handler(news,
                                lambda msg: check_message_text(msg, ['news']))

    dp.register_message_handler(news_by_date,
                                Text(startswith=['news'], ignore_case=True))

    dp.register_callback_query_handler(news_update,
                                       lambda call: 'news_update' in call.data)

    dp.register_callback_query_handler(look_info,
                                       lambda call: check_call(call, ['look_info'], ind=0))

    dp.register_message_handler(settings,
                                lambda msg: check_message_text(msg, ['settings']))

    dp.register_callback_query_handler(settings_edit,
                                       lambda call: check_call(call, ['s'], ind=-1))

    dp.register_callback_query_handler(info_button,
                                       lambda call: check_call(call, ['info_button']))

    dp.register_callback_query_handler(settings_change,
                                       lambda call: check_call(call, ['settings_change'], ind=0))

    dp.register_callback_query_handler(notice_info,
                                       lambda call: check_call(call, ['notice_info'], ind=0))

    dp.register_message_handler(notifications,
                                lambda msg: check_message_text(msg, ['notifications']))

    dp.register_callback_query_handler(notifications_returned,
                                       lambda call: check_call(call, ['n'], ind=-1))

    dp.register_message_handler(search,
                                Text(startswith=['search'], ignore_case=True))

    dp.register_callback_query_handler(search_edit,
                                       Text(startswith=['sch']))

    dp.register_callback_query_handler(close,
                                       lambda call: call.data == 'close',
                                       state='*')

    dp.register_message_handler(help_message,
                                commands=['help'],
                                state='*')

    dp.register_message_handler(show_keyboard,
                                commands=['keyboard'],
                                state='*')

    dp.register_message_handler(other_messages,
                                state='*')

    # dp.register_errors_handler(terminated_by_other_get_updates, exception=TerminatedByOtherGetUpdates)
