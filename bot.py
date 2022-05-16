import os
import re
import threading
import time
import aiohttp
import asyncio
import datetime
import pytz

from pprint import pprint

from loguru import logger
from timezonefinder import TimezoneFinder

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, Update
from aiogram.utils import executor
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import Throttled, NetworkError, MessageNotModified, MessageCantBeEdited, BotBlocked, TerminatedByOtherGetUpdates

from aiogram.dispatcher import FSMContext, DEFAULT_RATE_LIMIT
from aiogram.dispatcher.handler import CancelHandler, current_handler
from aiogram.dispatcher.filters import Text, IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage


# MY_MODULES
from telegram.keyboards import INLINE, REPLY

from data.postgres import CONNECT
from data.parse import UpdateData

from log.methods import CreateLog

from functions import UpdateData_by_timer
from functions import check_message_text, check_callback_split
from functions import get_timezone_text, get_correct_date

# CONFIG
from telegram.config import notifications_limits
from telegram.config import GOD_ID, ADMIN_IDS
from telegram.config import FLAG_SMILE, ANSWER_TEXT, ANSWER_CALLBACK
from telegram.config import RATE_LIMITS, rate_limit_default
from telegram.keyboards import URL

from data.config import MAIN_URL

from config import Intervals
from config import TOKEN, db_settings, log_settings
from config import WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT


#directory = os.getcwd()

log_file_local_path = log_settings['sink']


# Set logging
logger.add(**log_settings)


# Database connection
[TABLE, INSERT, UPDATE, SELECT, DELETE] = CONNECT(db_settings)

# UpdateData
#UpdateData_by_timer(INSERT, SELECT, UPDATE, UpdateData)


# Live notifications
LIVE_MATCHES = []

async def LiveNotifications():
    global LIVE_MATCHES

    live_matches_info = [x for x in SELECT.live_matches_for_notice() if x[0] not in LIVE_MATCHES]
    
    for match in live_matches_info:

        match_id = match[0]
        stars = match[1]
        team1_id = match[2]
        team1_name = match[3]
        team2_id = match[4]
        team2_name = match[5]
        event_id = match[6]
        event_name = match[7]

        preview_show = stars <= 0

        match_obj = (match_id, 'L', None, team1_name, team2_name, event_id, event_name, None)

        user_IDS = SELECT.user_ids_for_notice(match_id, team1_id, team2_id, event_id)

        for user_id in user_IDS:
            text = f"{fmt.hide_link(URL().match_or_analytics('M', match_id, team1_name, team2_name, event_name))}{ANSWER_TEXT['start_live']}"
            keyboard = INLINE().notice_start_live(match_obj)
            await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, disable_web_page_preview=preview_show)

    LIVE_MATCHES = live_matches_info


# News notifications

async def NewsNotifications():

    user_IDS = SELECT.user_ids_for_news_notice()

    news_object = SELECT.news(notice=True)
    
    for one_news in news_object:

        text = get_news_message([one_news])
        if text is None:
            continue
        
        keyboard = INLINE().news(update_button=False)

        for user_id in user_IDS:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)



def get_news_message(news_object, answer_text = ''):    
    for one_news in news_object:
        id_ = one_news[0]
        text = one_news[1]
        flag = one_news[2]
        href = one_news[3]

        url = URL().news(id_, href)

        answer_text += f"{flag} <a href='{url}'>{text}</a>\n\n"

    return None if answer_text == '' else answer_text



# DELETE OLD EVENTS
async def DeleteOldEvents():
    UPDATE.delete_old_events()





# Telegram
bot = Bot(token=TOKEN, parse_mode='html')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

BLOCKED_USERS = SELECT.blocked_user_ids()


class UserStates(StatesGroup):
    timezone_method = State()
    timezone = State()




# -------------------------------------------------------------------


# ANTIFLOOD

def rate_limit():
    def decorator(func):

        func_name = func.__name__

        limit = RATE_LIMITS.get(func_name, rate_limit_default)

        setattr(func, 'throttling_rate_limit', limit)
        setattr(func, 'throttling_key', func_name)
        
        return func
    return decorator


class ThrottlingMiddleware(BaseMiddleware):

    def __init__(self, limit=DEFAULT_RATE_LIMIT, key_prefix='antiflood_'):
        self.rate_limit = limit
        self.prefix = key_prefix
        super(ThrottlingMiddleware, self).__init__()

    async def on_process_message(self, message: Message, data: dict):

        handler = current_handler.get()

        dispatcher = Dispatcher.get_current()

        if handler:
            limit = getattr(handler, 'throttling_rate_limit', self.rate_limit)
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            limit = self.rate_limit
            key = f"{self.prefix}_message"

        try:
            await dispatcher.throttle(key, rate=limit)
        except Throttled as t:
            await self.message_throttled(message, t)

            raise CancelHandler()

    async def message_throttled(self, message: Message, throttled: Throttled):

        handler = current_handler.get()
        
        if handler:
            key = getattr(handler, 'throttling_key', f"{self.prefix}_{handler.__name__}")
        else:
            key = f"{self.prefix}_message"

        delta = throttled.rate - throttled.delta

        if throttled.exceeded_count <= 2:
            await message.answer('Stop spamming, otherwise you will be blocked')

        await asyncio.sleep(delta)


'''
фиксируем каждое превышение лимита, данные храним в оперативной памяти
как только количество превышений превысит порог, блочим юзера навсегда

'''


# BLOCKED_USERS - можно держать в оперативной памяти, чтобы не обращаться к бд

@dp.message_handler(lambda message: message.chat.id in BLOCKED_USERS)
async def message_from_blocked_user(message: Message):
    pass











# NEW USER  ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: SELECT.user_info(user_id=message.chat.id) is None)
async def new_user(message: Message, state: FSMContext, send_location_button = False):

    user_id = message.chat.id
    joined = message.date
    language = message['from']['language_code']

    try:
        name = message.chat.first_name
        text = ANSWER_TEXT["welcome_message_private"](name)
        send_location_button = True
    except:
        name = message.chat.title
        text = ANSWER_TEXT["welcome_message_group"](name)

    new_user_data = (user_id, language, name, joined)
    INSERT.new_user(new_user_data)
    
    await change_timezone(message, text=text, send_location_button=send_location_button)
    await state.update_data(send_help_message=True)
    CreateLog(message, 'new_user')



# CLOSE ------------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: callback.data == 'close', state='*')
async def close(callback: CallbackQuery):
    await callback.message.delete()
    CreateLog(callback, 'close')



# HELP -------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['help'], state='*')
#@rate_limit()
async def help(message: Message):
    await message.answer(ANSWER_TEXT['help'])


# TIMEZONE -----------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['start', 'change_timezone'])
#@rate_limit()
async def change_timezone(message: Message, text = None, send_location_button = False):
    
    if text is None:
        if message.chat.type == 'private':
            text = ANSWER_TEXT["change_timezone_private"]
            send_location_button = True
        elif message.chat.type == 'group':
            text = ANSWER_TEXT["change_timezone_group"]
        
    keyboard = REPLY().location(send_location_button=send_location_button)

    await message.answer(text, reply_markup=keyboard)
    await UserStates.timezone_method.set()
    CreateLog(message, 'change_timezone')


@dp.message_handler(Text(contains='selection timezone', ignore_case=True), state=UserStates.timezone_method)
#@rate_limit()
async def selection_timezone(message: Message):
    
    text = ANSWER_TEXT["selection_timezone"]
    keyboard = INLINE(row_width=2).timezones()
    
    await message.answer(text, reply_markup=keyboard)
    await UserStates.timezone.set()
    CreateLog(message, 'selection_timezone')


@dp.message_handler(content_types=['location'], state='*')
async def location(message: Message, state: FSMContext):

    user_id = message.chat.id
    
    await message.answer_chat_action('find_location')
    await asyncio.sleep(1)
    
    location = TimezoneFinder().timezone_at(lng=message.location.longitude, lat=message.location.latitude)
    user_timezone = datetime.datetime.now(pytz.timezone(location)).utcoffset()
    timezone_text = get_timezone_text(user_timezone)
    
    text = ANSWER_TEXT["location"](location, timezone_text)
    keyboard = REPLY().default()

    await message.answer(text, reply_markup=keyboard)
    await state.finish()

    UPDATE.user_timezone(user_id, user_timezone)
    CreateLog(message, 'location', params=timezone_text)


@dp.callback_query_handler(Text(contains=[':00']), state=UserStates.timezone)
#@rate_limit()
async def timezone(callback: CallbackQuery, state: FSMContext):

    [timezone_text, user_timezone] = get_timezone_text(callback.data, interval=True)    

    # удаляем сообщение только в приватном чате
    if callback.message.chat.type == 'private':
        await callback.message.delete()
    else:
        await callback.message.edit_text(message.text, reply_markup=None)

    text = ANSWER_TEXT["timezone"](timezone_text)
    keyboard = REPLY().default()

    UPDATE.user_timezone(callback.message.chat.id, user_timezone)

    await callback.message.answer(text, reply_markup=keyboard)    
    
    user_data = await state.get_data()
    if 'send_help_message' in user_data:
        await asyncio.sleep(2)
        await help(callback.message)

    await state.finish()
    
    CreateLog(callback, 'timezone', params=timezone_text)


@dp.message_handler(state=UserStates.timezone_method)
#@rate_limit()
async def error_location_selection_message(message: Message):
    await message.answer(ANSWER_TEXT["error_location_selection"])
    CreateLog(message, 'error_location_selection')


@dp.callback_query_handler(state=UserStates.timezone_method)
#@rate_limit()
async def error_location_selection_callback(callback: CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_TEXT['error_location_selection'])


@dp.message_handler(state=UserStates.timezone)
#@rate_limit()
async def error_location_send(message: Message):
    await message.answer(ANSWER_TEXT['error_location_send'])
    CreateLog(message, 'error_location_send')


@dp.callback_query_handler(state=UserStates.timezone)
#@rate_limit()
async def error_location_send_callback(callback: CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_TEXT['error_location_send'])


# NOTICE ----------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['notice'], ind=0))
#@rate_limit()
async def notice(callback: CallbackQuery):

    callback_data_split = callback.data.split()

    user_id = callback.message.chat.id
    type_notice = {'mi': 'matches', 'ei': 'events', 'ti': 'teams'}.get(callback_data_split[-2], False)
    id_ = callback_data_split[-1]

    if not type_notice:
        return

    limit = notifications_limits(type_notice)

    update_result, limit_condition = UPDATE.user_notice(user_id, type_notice, id_, limit=limit)

    print(update_result, limit_condition)

    if limit_condition:
        text = ANSWER_CALLBACK['notice_limit'](type_notice, limit)
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)
    elif update_result:
        text = ANSWER_CALLBACK['notice_by_type'](type_notice)
    else:
        text = ANSWER_CALLBACK['notice_deleted']
    
    await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    if type_notice == 'matches':
        await match_info(callback)
    
    elif type_notice == 'events':
        await event_info(callback)

    elif type_notice == 'teams':
        await team_info(callback)




# LIVE ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['live']))
#@rate_limit()
async def live_matches(message: Message, callback = None):
    
    matches_array = SELECT.live_matches()

    date_ = datetime.datetime.today().date()
    last_callback_data = f"d L m {date_}"

    text = ANSWER_TEXT['live_matches']
    if not len(matches_array):
        text = ANSWER_TEXT['no_live_matches']
    keyboard = INLINE().matches(matches_array, last_callback_data)
    
    if callback is None:
        return await message.answer(text, reply_markup=keyboard)

    if not matches_array:
        return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_live_broadcasts'])
    
    await message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)
    
    CreateLog(message, 'live_matches')




# DATES ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['matches', 'results'])
#@rate_limit()
async def dates_by_match_type(message: Message, callback = None, match_type = None, text = None, edit_message = False):

    user_id = message.chat.id
    [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])

    # если нет информации о типе матча
    if match_type is None:
        match_type = 'U' if '/matches' in message.text else 'R'

    dates_array_sorted = SELECT.dates(user_timezone, match_type)

    if not len(dates_array_sorted) and edit_message:
        return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_dates'])

    if text is None:
        text = ANSWER_TEXT['dates_text_by_match_type'](match_type)
    keyboard = INLINE().dates(match_type, dates_array_sorted)

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
        return await bot.answer_callback_query(callback.id)
    
    await message.answer(text, reply_markup=keyboard)
    
    CreateLog(message, 'dates_by_match_type')


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['d']))
#@rate_limit()
async def dates(callback: CallbackQuery, match_type = None, text = None, edit_message = True):
    if isinstance(callback, CallbackQuery):
        message = callback.message
        match_type = callback.data.split()[1]
    else:
        message = callback
        edit_message = False

    try:
        await dates_by_match_type(message, match_type=match_type, text=text, edit_message=edit_message, callback=callback)
    except MessageNotModified:
        await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_matches_by_type'](match_type))



# MATCHES ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['today', 'tomorrow', 'results today', 'results_today', 'results yesterday', 'results_yesterday']))
#@rate_limit()
async def matches_or_results(message: Message):
    
    user_id = message.chat.id

    match_type = 'U' if check_message_text(message, ['today', 'tomorrow']) else 'R'
    [user_timezone, stars_matches_display] = SELECT.user_data_by_colomn_names(user_id, ['timezone, stars_matches_display'])
    date_ = (datetime.datetime.utcnow() + user_timezone).date()

    if check_message_text(message, ['tomorrow']):
        date_ += datetime.timedelta(days=1)
    elif check_message_text(message, ['results yesterday', 'results_yesterday']):
        date_ += datetime.timedelta(days=-1)

    await matches_by_date(message, match_type=match_type, date_=date_, user_timezone=user_timezone, stars_matches_display=stars_matches_display)


@dp.message_handler(Text(startswith=['matches', 'results'], ignore_case=True))
#@rate_limit()
async def matches_by_user_date(message: Message):

    user_id = message.chat.id

    command_split = message.text.split()
    match_type = {'matches': 'U'}.get(command_split[0].lower(), 'R')

    [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])
    
    date_text = command_split[-1].replace('/', '.').replace('-', '.')
    date_ = get_correct_date(date_text)

    if date_ is None:
        return await message.answer(ANSWER_TEXT['correct_date'])

    return await matches_by_date(message, match_type=match_type, date_=date_, user_timezone=user_timezone)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['m']))
#@rate_limit()
async def matches_by_date(callback: CallbackQuery, match_type = None, date_ = None, user_timezone = None, stars_matches_display = 0):

    if isinstance(callback, CallbackQuery):
        last_callback_data = callback.data
        callback_data_split = callback.data.split()
       
        match_type = callback_data_split[1]
        
        if match_type == 'L':
            return await live_matches(callback.message, callback=callback)

        date_text = callback_data_split[3]
        date_ = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
        
        user_id = callback.message.chat.id
        [user_timezone, stars_matches_display] = SELECT.user_data_by_colomn_names(user_id, ['timezone', 'stars_matches_display'])
    else:
        user_id = callback.chat.id
        last_callback_data = f"d {match_type} m {date_}"
        [stars_matches_display] = SELECT.user_data_by_colomn_names(user_id, ['stars_matches_display'])

    matches_array = SELECT.matches(match_type, date_, user_timezone, stars_matches_display)

    if not len(matches_array):
        text = ANSWER_TEXT['no_matches_by_type'](match_type)
        return await dates(callback, match_type=match_type, text=text)
    
    text = ANSWER_TEXT['matches_by_type'](match_type) + ANSWER_TEXT['filter_info']({'stars': stars_matches_display})
    keyboard = INLINE().matches(matches_array, last_callback_data, date_=date_)
    
    if isinstance(callback, Message):
        await bot.send_message(chat_id=callback.chat.id, text=text, reply_markup=keyboard)
    else:
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
            await bot.answer_callback_query(callback.id)
        except MessageNotModified:
            text = ANSWER_CALLBACK['no_information_matches'](match_type)
            await bot.answer_callback_query(callback_query_id=callback.id, text=text)
    CreateLog(callback, 'matches_by_date', params=f"{match_type} {date_}")


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['um', 'rm']))
#@rate_limit()
async def matches_by_team_id(callback: CallbackQuery):
    
    user_id = callback.message.chat.id

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()
    match_type = {'um': 'U', 'rm': 'R'}.get(callback_data_split[-2], 'U')
    team_id = callback_data_split[-1]

    [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])
    matches_array = SELECT.matches_by_team_id(team_id, match_type, user_timezone)

    if not len(matches_array):
        text = ANSWER_CALLBACK['no_matches_by_type'](match_type)
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = ANSWER_TEXT['matches_by_team'](match_type)
    keyboard = INLINE().matches_by_team_id(matches_array, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)




@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['mi']))
#@rate_limit()
async def match_info(callback: CallbackQuery):

    user_id = callback.message.chat.id

    last_callback_data = callback.data.replace('notice ', '')
    match_id = last_callback_data.split()[-1]
    
    [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])
    subscription = SELECT.notice('matches', user_id, match_id)
    match_info_obj = SELECT.match_info(match_id, user_timezone)

    text = ANSWER_TEXT['match_info']
    keyboard = INLINE().match_info(match_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)
    CreateLog(callback, 'match_info', params=match_id)




# TEAMS -------------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ti']))
#@rate_limit()
async def team_info(callback: Message):

    user_id = callback.message.chat.id

    last_callback_data = callback.data.replace('notice ', '')
    team_id = last_callback_data.split()[-1]

    if team_id == 'None':
        text = ANSWER_CALLBACK['no_team_data']
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    subscription = SELECT.notice('teams', user_id, team_id)
    team_info_obj = SELECT.team_info(team_id)

    text = ANSWER_TEXT['team_info']
    keyboard = INLINE().team_info(team_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['dt']))
async def details_by_team(callback: CallbackQuery):

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    team_id = callback_data_split[-1]

    details_info = SELECT.details_by_team(team_id)

    text = ANSWER_TEXT['details_by_team']
    keyboard = INLINE().details_by_team(details_info, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)



# PLAYERS -----------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['pi']))
#@rate_limit()
async def player_info(callback: Message):

    user_id = callback.message.chat.id

    last_callback_data = callback.data#.replace('notice ', '')
    player_id = last_callback_data.split()[-1]

    if player_id == 'None':
        text = ANSWER_CALLBACK['no_player_data']
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    #subscription = SELECT.notice('players', user_id, player_id)
    player_info_obj = SELECT.player_info(player_id)

    text = ANSWER_TEXT['player_info']
    keyboard = INLINE().player_info(player_info_obj, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


# EVENTS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['events']))#Text(startswith='events', ignore_case=True))
#@rate_limit()
async def events(message: Message, callback = None, edit_message = False):

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
        return await bot.answer_callback_query(callback.id)
    await message.answer(text, reply_markup=keyboard)


def events_type():
    text = ANSWER_TEXT['events_type']
    keyboard = INLINE(row_width=1).events_type()
    return text, keyboard



def get_event_date(date_text, format_="%m.%Y"):
    try:
        if len(date_text.split('.')) == 1:
            date_text = f"{date_text}.{datetime.datetime.now().year}"
        return date_text, datetime.datetime.strptime(date_text, format_).date()
    except:
        return date_text, None




def events_by_date(message_text_split, keyboard = None):
    date_text = message_text_split[-1].replace('/', '.').replace('-', '.')
    
    date_text, date_ = get_event_date(date_text)

    if date_ is None:
        text = ANSWER_TEXT['correct_date_events']
        return text, keyboard

    events_array = SELECT.events_by_date(date_text)

    if not len(events_array):
        text = ANSWER_TEXT['no_events_by_date']
        return text, keyboard
    
    last_callback_data = f"ebd {date_text}"

    date_text = datetime.datetime.strftime(date_, "%B %Y")
    text = ANSWER_TEXT['events_by_date'](date_text)
    keyboard = INLINE().events_by_date(events_array, last_callback_data)

    return text, keyboard



@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ebd']))
async def events_by_date_edit(callback: CallbackQuery):
    await events(callback.message, callback=callback, edit_message=True)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['et'], ind=-1))
#@rate_limit()
async def events_type_edit(callback: CallbackQuery):
    text, keyboard = events_type()
    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ebt']))
#@rate_limit()
async def events_by_type(callback: CallbackQuery):
    
    last_callback_data = callback.data
    event_type = last_callback_data.split()[-1]
    
    events_array = SELECT.events_by_type(event_type)

    if not len(events_array):
        text = ANSWER_CALLBACK['no_events_by_type'](event_type)
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = ANSWER_TEXT['text_by_event_type'](event_type)
    keyboard = INLINE(row_width=1).events(event_type, events_array, last_callback_data, add_months=event_type != 'O')

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['etm']))
async def events_by_team(callback: CallbackQuery):

    last_callback_data = callback.data
    team_id = last_callback_data.split()[-1]

    events_array = SELECT.events_by_team(team_id)

    if not len(events_array):
        text = ANSWER_CALLBACK['no_events_by_team']
        return await bot.answer_callback_query(callback_query_id=callback.id, text=text)

    text = ANSWER_TEXT['events_by_team']
    keyboard = INLINE(row_width=1).events_by_team(events_array, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ei']))
#@rate_limit()
async def event_info(callback: CallbackQuery):

    last_callback_data = callback.data.replace('notice ', '')
    event_id = last_callback_data.split()[-1]

    if event_id == 'None':
        return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_event_data'])

    user_id = callback.message.chat.id
    subscription = SELECT.notice('events', user_id, event_id)

    event_info_obj = SELECT.event_info(event_id)

    text = ANSWER_TEXT['event_info']
    keyboard = INLINE().event_info(event_info_obj, last_callback_data, subscription)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['em'], ind=-1)) 
#@rate_limit()
async def event_matches(callback: CallbackQuery):

    user_id = callback.message.chat.id

    last_callback_data = callback.data
    event_id = last_callback_data.split()[-2]

    [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])
    matches_by_event_id_array = SELECT.matches_by_event_id(event_id, user_timezone)

    if not len(matches_by_event_id_array):
        return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_event_matches'])

    text = ANSWER_TEXT['matches_for_event']
    keyboard = INLINE().matches(matches_by_event_id_array, last_callback_data, add_live_mark=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    await bot.answer_callback_query(callback.id)




# NEWS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['news']))
#@rate_limit()
async def news(message: Message, callback = None, date_ = None, date_for_message = ''):    
    
    news_object = SELECT.news(date_=date_)

    text = get_news_message(news_object, answer_text=date_for_message)

    if not len(news_object):
        await message.answer(ANSWER_TEXT['no_news'])    

    elif not callback is None:
        try:
            await message.edit_text(text, reply_markup=INLINE().news(), disable_web_page_preview=True)
        except MessageNotModified:
            text = ANSWER_CALLBACK['no_new_news']
            await bot.answer_callback_query(callback_query_id=callback.id, text=text)
    else:
        update_button = date_ is None # нет необходимости обновлять новости о прошедших днях
        await message.answer(text, reply_markup=INLINE().news(update_button=update_button), disable_web_page_preview=True)


@dp.message_handler(Text(startswith=['news'], ignore_case=True))
#@rate_limit()
async def news_by_date(message: Message):
    
    date_text = message.text.split()[-1].replace('/', '.').replace('-', '.')
    date_ = get_correct_date(date_text)

    if date_ is None:
        text = ANSWER_TEXT['correct_date']
        return await message.answer(text)

    date_for_message = f"<code>{datetime.datetime.strftime(date_, '%d %B %Y')}</code>\n\n"

    await news(message, date_=date_, date_for_message=date_for_message) 


@dp.callback_query_handler(lambda callback: 'news_update' in callback.data)
#@rate_limit()
async def news_update(callback: CallbackQuery):
    await news(callback.message, callback = callback)





# INFO ---------------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['look_info'], ind=0)) 
#@rate_limit()
async def look_info(callback: CallbackQuery):

    text = callback.data.replace('look_info ', '')

    await bot.answer_callback_query(callback_query_id=callback.id, text=text, show_alert=True)




# SETTINGS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['settings']))
async def settings(message: Message, edit = False):

    user_settings_info = SELECT.user_settings(message.chat.id)

    text = ANSWER_TEXT['settings']
    keyboard = INLINE().settings(user_settings_info)
    
    if edit:
        return await message.edit_text(text, reply_markup=keyboard)
    await message.answer(text, reply_markup=keyboard)
    
    CreateLog(message, 'settings')


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['s'], ind=-1))
async def settings_edit(callback: CallbackQuery):
    await settings(callback.message, edit=True)
    await bot.answer_callback_query(callback.id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['info_button']))
async def info_button(callback: CallbackQuery):

    # config
    info_button_descriptions = {'timezone': "Choose timezone",
                                  'notifications': "View subscriptions",
                                  'receive_notices': "Receive notifications about signed matches",
                                  'news_notice': "Receive news notifications",
                                  'delete_old_matches': "Remove past matches from the list of subscriptions",
                                  'delete_old_events': "Remove past events from the list of subscriptions",
                                  'stars_matches_display': "Show matches only with a certain rating (stars)",

                                  'number_maps': "Number of maps played",
                                  'number_rounds': "Number of rounds played",
                                  'kd_diff': "",
                                  'kd': "",
                                  'rating': ""
                                    }

    info_parameter = callback.data.split()[-1]

    text = info_button_descriptions.get(info_parameter, "No information")

    await bot.answer_callback_query(callback_query_id=callback.id, text=text, show_alert=True)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['settings_change'], ind=0))
async def settings_change(callback: CallbackQuery):
    
    user_id = callback.message.chat.id
    variable_parameter = callback.data.split()[-1]

    if variable_parameter == 'timezone':
        await callback.message.delete()
        return await change_timezone(callback.message)

    elif variable_parameter in ['receive_notices', 'news_notice', 'delete_old_matches', 'delete_old_events']:
        UPDATE.user_bool_parameter(user_id, variable_parameter)
        await settings(callback.message, edit=True)

    elif variable_parameter == 'stars_matches_display':
        UPDATE.stars_matches_display(user_id)
        await settings(callback.message, edit=True)
    
    await bot.answer_callback_query(callback.id)

    CreateLog(callback, 'settings_change', params=variable_parameter)



# NOTICE ----------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['notice_info'], ind=0))
#@rate_limit()
async def notice_info(callback: CallbackQuery):

    type_notice = callback.data.split()[-1]
    text = ANSWER_CALLBACK['notice_info_by_type'](type_notice)

    await bot.answer_callback_query(callback_query_id=callback.id, text=text, show_alert=True)


@dp.message_handler(lambda message: check_message_text(message, ['notifications']))
#@rate_limit()
async def notifications(message: Message, edit = False, last_callback_data = 'n', add_back_button = False):

    user_id = message.chat.id

    all_notice_obj = SELECT.all_notice(user_id)
    
    d = {'teams': [], 'matches': [], 'events': []}
    for i in (0,2,4):
        notice_type = all_notice_obj[i]
        ids_array = all_notice_obj[i+1]
        
        if ids_array is None or ids_array == []:
            continue

        ids_array_sorted = sorted(ids_array)
        
        if notice_type == 'teams':
            d[notice_type] = SELECT.teams_by_ids_array(ids_array_sorted)

        elif notice_type == 'matches':
            [user_timezone] = SELECT.user_data_by_colomn_names(user_id, ['timezone'])
            d[notice_type] = SELECT.matches_by_ids_array(ids_array_sorted, user_timezone)

        elif notice_type == 'events':
            d[notice_type] = SELECT.events_by_ids_array(ids_array_sorted)

    text = ANSWER_TEXT['notifications']
    keyboard = INLINE().notifications(d, last_callback_data, add_team_flag=True)

    if edit:
        return await message.edit_text(text, reply_markup=keyboard)
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['n'], ind=-1))
#@rate_limit()
async def notifications_returned(callback: CallbackQuery):
    last_callback_data = callback.data
    await notifications(callback.message, last_callback_data=last_callback_data, edit=True)



# SEARCH ---------------------------------------------------------------------------------------------------------------------------------------------------

# объединить всё в одну функцию

@dp.message_handler(Text(startswith=['search'], ignore_case=True))
#@rate_limit()
async def search(message: Message, callback = None, type_search_short = None, name_search = None, edit = False):

    if name_search is None:
        message_text_lower = message.text.lower()
        try:
            type_search = message_text_lower.split()[1]
        except:
            type_search = None
        name_search = message.text.lower().replace(f"search {type_search} ", '')
        type_search_short = {'team': 't', 'player': 'p'}.get(type_search, None)

    if type_search_short is None:
        text = ANSWER_TEXT['search_type_correct']
        return await message.answer(text)
    
    if len(name_search) < 3 or not re.match("^[A-Za-z0-9-.']*$", name_search):
        text = ANSWER_TEXT['search_enter_correct'](type_search)
        return await message.answer(text)

    if type_search_short == 't':
        all_coincidences = SELECT.teams_by_name(name_search)
    elif type_search_short == 'p':
        all_coincidences = SELECT.player_id_by_name(name_search)

    if not len(all_coincidences):
        text = ANSWER_TEXT['search_not_found'](type_search)
        return await message.answer(text) 

    last_callback_data = f"sch {type_search_short} {name_search}"

    text = ANSWER_TEXT['search_results'](name_search)
    
    if type_search_short == 't':
        keyboard = INLINE().teams_list(all_coincidences, last_callback_data, add_flag=True)
    elif type_search_short == 'p':
        keyboard = INLINE().players_list(all_coincidences, last_callback_data)

    if edit and not callback is None:
        await callback.message.edit_text(text, reply_markup=keyboard)
        return await bot.answer_callback_query(callback.id)
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(Text(startswith=['sch']))
#@rate_limit()
async def search_edit(callback: CallbackQuery):
    callback_data_split = callback.data.split()
    type_search_short = callback_data_split[1]
    name_search = callback_data_split[2]
    await search(callback.message, callback=callback, type_search_short=type_search_short, name_search=name_search, edit=True)





# KEYBOARD ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['keyboard'])
#@rate_limit()
async def show_keyboard(message: Message):
    await message.answer(ANSWER_TEXT["keyboard"], reply_markup=REPLY().default())
    CreateLog(message, 'show_keyboard')







# NOT CLICKABLE
@dp.callback_query_handler()
#@rate_limit()
async def button_not_clickable(callback: CallbackQuery):
    print(callback.data)
    #await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK["button_not_clickable"])
    #CreateLog(callback, 'button_not_clickable')
    await callback.message.delete()




# EXCEPTION -----------------------------------------------------------------------------------------------------------------------------
'''
@dp.errors_handler(exception=BotBlocked)
async def bot_blocked(update: Update, exception: BotBlocked):
    logger.info(f"[EXCEPTION] [{exception}] {update}")
    #await exception_log(update, exception)
'''


@dp.errors_handler(exception=TerminatedByOtherGetUpdates)
async def terminated_by_other_get_updates(update: Update, exception: BotBlocked):
    await bot.send_message(chat_id=GOD_ID, text='КТО-ТО ВОСПОЛЬЗОВАЛСЯ ТОКЕНОМ!!!')





# ADMINS --------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(IDFilter(chat_id=ADMIN_IDS))
async def admin_commands(message: Message):

    message_text =  message.text.lower()
    message_text_split = message_text.split()
    command = message_text_split[0]

    if command == 'update':
        UpdateData(INSERT, SELECT, UPDATE, message_text_split[1:])
        await message.answer(f"The bot has updated the data about {message_text_split[1:]}")

    elif command == 'get':
        if message_text_split[1] == 'log':
            await bot.send_document(chat_id=message.chat.id, document=open(log_file_local_path, 'rb'))

        elif message_text_split[1] == 'stat':
            print('stat')



    elif command == 'psql':
        query = message_text.replace(command, '')
        result = TABLE.your_request(query)
        await message.answer(query)
        await message.answer(result)





# WEBHOOK ------------------------------------------------------------------------------------------------------------------------------
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()





def repeat(func, loop):
    asyncio.ensure_future(func(), loop=loop)
    interval = Intervals(func.__name__)
    loop.call_later(interval, repeat, func, loop)






def main():
    while True:

        #dp.middleware.setup(LoggingMiddleware())
        dp.middleware.setup(ThrottlingMiddleware())

        loop = asyncio.get_event_loop()
        loop.call_later(5, repeat, LiveNotifications, loop)

        loop.call_later(5, repeat, NewsNotifications, loop)

        loop.call_later(5, repeat, DeleteOldEvents, loop)

        executor.start_polling(dp, skip_updates=True)
        
        '''
        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )
        '''




if __name__ == '__main__':
    main()
    

    

    


'''
использовать shedule для рассылки по расписанию
import aiogram.utils.markdown as fmt
fmt.hide_link(url)

'''