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
#from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound, TerminatedByOtherGetUpdates
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
from telegram.config import GOD_ID, ADMIN_IDS
from telegram.config import FLAG_SMILE, ANSWER_TEXT, ANSWER_CALLBACK
from telegram.config import RATE_LIMITS, rate_limit_default

from data.config import MAIN_URL

from config import TOKEN, db_settings, log_settings
from config import WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT




#directory = os.getcwd()

log_file_local_path = log_settings['sink']


# Set logging
logger.add(**log_settings)


# Database connection
[TABLE, INSERT, UPDATE, SELECT, DELETE] = CONNECT(db_settings)

# UpdateData
UpdateData_by_timer(INSERT, SELECT, UpdateData)


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
async def new_user(message: Message, send_location_button = False):

    user_id = message.chat.id
    joined = message.date
    try:
        name = message.chat.first_name
        text = ANSWER_TEXT["welcome_message_private"](name)
        send_location_button = True
    except:
        name = message.chat.title
        text = ANSWER_TEXT["welcome_message_group"](name)

    new_user_data = (user_id, name, joined)
    INSERT.new_user(new_user_data)
    
    await change_timezone(message, text=text, send_location_button=send_location_button)
    CreateLog(message, 'new_user')



# CLOSE ------------------------------------------------------------------------------------------------------------------------------
@dp.callback_query_handler(lambda callback: callback.data == 'close')
async def close(callback: CallbackQuery):
    await callback.message.delete()
    CreateLog(callback, 'close')



# HELP -------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['help'])
@rate_limit()
async def help(message: Message):
    await message.answer(ANSWER_TEXT['help'])


# TIMEZONE -----------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['start', 'change_timezone'])
@rate_limit()
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
@rate_limit()
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


@dp.message_handler(state=UserStates.timezone_method)
@rate_limit()
async def error_location_selection(message: Message):
    await message.answer(ANSWER_TEXT["error_location_selection"])
    CreateLog(message, 'error_location_selection')


@dp.callback_query_handler(state=UserStates.timezone)
@rate_limit()
async def timezone(callback: CallbackQuery, state: FSMContext):

    [timezone_text, user_timezone] = get_timezone_text(callback.data, interval=True)    

    # удаляем сообщение только в приватном чате
    if callback.message.chat.type == 'private':
        await callback.message.delete()
    else:
        await callback.message.edit_text(message.text, reply_markup=None)

    text = ANSWER_TEXT["timezone"](timezone_text)
    keyboard = REPLY().default()

    await callback.message.answer(text, reply_markup=keyboard)
    await state.finish()
    UPDATE.user_timezone(callback.message.chat.id, user_timezone)
    CreateLog(callback, 'timezone', params=timezone_text)
    

@dp.message_handler(state=UserStates.timezone)
@rate_limit()
async def error_location_send(message: Message):
    await message.answer(ANSWER_TEXT['error_location_send'])
    CreateLog(message, 'error_location_send')




# LIVE ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['live']))
@rate_limit()
async def live_matches(message: Message, callback = None):
    
    matches_array = SELECT.live_matches()
    date_ = datetime.datetime.today().date()
    last_callback_data = f"d L m {date_}"

    text = ANSWER_TEXT['live_matches']
    keyboard = INLINE().matches(matches_array, last_callback_data)
    
    try:
        await message.edit_text(text, reply_markup=keyboard)
    except:
        if callback is None:
            await message.answer(text, reply_markup=keyboard)
        else:
            await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_live_broadcasts'])
            
    CreateLog(message, 'live_matches')




# DATES ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['matches', 'results'])
@rate_limit()
async def dates_by_match_type(message: Message, match_type = None, edit_message = False):

    user_timezone = SELECT.user_timezone(message.chat.id)

    # если нет информации о типе матча
    if match_type is None:
        match_type = 'U' if '/matches' in message.text else 'R'

    dates_array_sorted = SELECT.dates(user_timezone, match_type)

    text = ANSWER_TEXT['dates_text_by_match_type'](match_type)
    keyboard = INLINE().dates(match_type, dates_array_sorted)

    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)
    CreateLog(message, 'dates_by_match_type')


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['d']))
@rate_limit()
async def dates(callback: CallbackQuery):
    match_type = callback.data.split()[1]
    await dates_by_match_type(callback.message, match_type=match_type, edit_message=True)




# MATCHES ------------------------------------------------------------------------------------------------------------------------------

@dp.message_handler(lambda message: check_message_text(message, ['today', 'tomorrow', 'results today', 'results_today']))
@rate_limit()
async def matches_or_results(message: Message):
        
    match_type = 'U' if check_message_text(message, ['today', 'tomorrow']) else 'R'
    user_timezone = SELECT.user_timezone(message.chat.id)
    date_ = (datetime.datetime.utcnow() + user_timezone).date()

    if check_message_text(message, ['tomorrow']):
        date_ += datetime.timedelta(days=1)

    await matches_by_date(message, match_type=match_type, date_=date_, user_timezone=user_timezone)


@dp.message_handler(Text(startswith=['matches', 'results'], ignore_case=True))
@rate_limit()
async def command_with_date(message: Message):

    command_split = message.text.split()
    match_type = 'U' if command_split[0].lower() == 'matches' else 'R'

    user_timezone = SELECT.user_timezone(message.chat.id)
    
    date_text = command_split[-1].replace('/', '.')
    date_ = get_correct_date(date_text)

    if date_ is None:
        return await message.answer(ANSWER_TEXT['correct_date'])

    return await matches_by_date(message, match_type=match_type, date_=date_, user_timezone=user_timezone)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['m']))
@rate_limit()
async def matches_by_date(callback: CallbackQuery, match_type = None, date_ = None, user_timezone = None):

    if isinstance(callback, CallbackQuery):
        last_callback_data = callback.data
        callback_data_split = callback.data.split()

        match_type = callback_data_split[1]
        
        if match_type == 'L':
            return await live_matches(callback.message, callback=callback)

        date_text = callback_data_split[3]
        date_ = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
        
        user_timezone = SELECT.user_timezone(callback.message.chat.id)
    else:
        last_callback_data = f"d {match_type} m {date_}"

    matches_array = SELECT.matches(match_type, date_, user_timezone)
    
    text = ANSWER_TEXT['matches_by_type'](match_type)
    keyboard = INLINE().matches(matches_array, last_callback_data, date_=date_)
    
    if len(matches_array) == 0:
        text = ANSWER_TEXT['no_matches_by_type'](match_type)

    if isinstance(callback, Message):
        await bot.send_message(chat_id=callback.chat.id, text=text, reply_markup=keyboard)
    else:
        try:
            await callback.message.edit_text(text, reply_markup=keyboard)
        except MessageNotModified:
            text = ANSWER_CALLBACK['no_information_matches'](match_type)
            await bot.answer_callback_query(callback_query_id=callback.id, text=text)
    CreateLog(callback, 'matches_by_date', params=f"{match_type} {date_}")


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['mi']))
@rate_limit()
async def match_info(callback: CallbackQuery):

    user_id = callback.message.chat.id

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    scorebot_id = callback_data_split[-1]
    
    user_timezone = SELECT.user_timezone(user_id)
    #user_subscriptions = SELECT.user_subscriptions(user_id)
    match_info_obj = SELECT.match_info(scorebot_id, user_timezone)

    text = ANSWER_TEXT['match_info']
    keyboard = INLINE().match_info(match_info_obj, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='html')
    CreateLog(callback, 'match_info', params=scorebot_id)




# EVENTS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(lambda message: check_message_text(message, ['events']))
@rate_limit()
async def events_type(message: Message, edit_message = False):
    
    text = ANSWER_TEXT['events_type']
    keyboard = INLINE(row_width=1).events_type()
    
    if edit_message:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)
    CreateLog(message, 'events_type')


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['events_type']))
@rate_limit()
async def events_type_edit(callback: CallbackQuery):
    await events_type(callback.message, edit_message=True)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['events_by_type']))
@rate_limit()
async def events_by_type(callback: CallbackQuery):
    
    event_type = callback.data.split()[1]
    
    if event_type == 'O':
        events_array = SELECT.events_by_type_ongoing()
    else:
        events_array = SELECT.events_by_type(event_type)

    text = ANSWER_TEXT['text_by_event_type'](event_type)
    keyboard = INLINE(row_width=1).events_by_type(events_array, callback.data)

    await callback.message.edit_text(text, reply_markup=keyboard)
    CreateLog(callback, 'events_by_type', params=event_type)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['ei']))
@rate_limit()
async def event_info(callback: CallbackQuery):

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    event_id = callback_data_split[-1]

    if event_id == 'None':
        return await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_event_data'])

    event_info_obj = SELECT.event_info(event_id)

    text = ANSWER_TEXT['event_info']
    keyboard = INLINE().event_info(event_info_obj, last_callback_data)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='html')
    CreateLog(callback, 'event_info', params=event_id)


@dp.callback_query_handler(lambda callback: check_callback_split(callback, ['em'])) 
@rate_limit()
async def event_matches(callback: CallbackQuery):

    last_callback_data = callback.data
    callback_data_split = last_callback_data.split()

    event_id = callback_data_split[-1]

    user_timezone = SELECT.user_timezone(callback.message.chat.id)
    matches_by_event_id_array = SELECT.matches_by_event_id(event_id, user_timezone)

    text = ANSWER_TEXT['matches_for_event']
    keyboard = INLINE().matches(matches_by_event_id_array, last_callback_data, live_mark=True)

    await callback.message.edit_text(text, reply_markup=keyboard)
    CreateLog(callback, 'event_matches', params=event_id)




# NEWS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['news'])
@rate_limit()
async def news(message: Message, date_ = None, callback = None):
    answer_text = ''
    
    news_object = SELECT.news(date_=date_)
    for one_news in news_object:
        id_ = one_news[0]
        text = one_news[1]
        flag = one_news[2]
        href = one_news[3]

        url = f"{MAIN_URL}news/{id_}/{href}"

        answer_text += f"{flag} <a href='{url}'>{text}</a>\n\n"

    if answer_text == '':
        await message.answer(ANSWER_TEXT['no_news'])

    elif not callback is None:
        try:
            await message.edit_text(answer_text, reply_markup=INLINE().news(), disable_web_page_preview=True)
        except MessageNotModified:
            await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK['no_new_news'])
    else:
        update_button = True if date_ is None else False
        await message.answer(answer_text, reply_markup=INLINE().news(update_button=update_button), disable_web_page_preview=True)

    CreateLog(message, 'news')


@dp.message_handler(Text(startswith=['news'], ignore_case=True))
@rate_limit()
async def news_by_date(message: Message):
    
    date_text = message.text.split()[-1].replace('/', '.')
    if date_text == 'news':
        return await news(message)
    date_ = get_correct_date(date_text)

    if date_ is None:
        return await message.answer(ANSWER_TEXT['correct_date'])
    await news(message, date_=date_) 


@dp.callback_query_handler(lambda callback: 'news_update' in callback.data)
@rate_limit()
async def news_update(callback: CallbackQuery):
    await news(callback.message, callback = callback)




# SETTINGS ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['settings'])
async def settings(message: Message, edit_message = False):

    user_info = SELECT.user_settings(message.chat.id)
    keyboard = INLINE().settings(user_info)
    if edit_message:
        await message.edit_text(ANSWER_TEXT['settings'], reply_markup=keyboard)
    else:
        await message.answer(ANSWER_TEXT['settings'], reply_markup=keyboard)
    CreateLog(message, 'settings')


@dp.callback_query_handler(lambda callback: 'settings info' in callback.data)
async def settings_info(callback: CallbackQuery):


    # config
    settings_info_descriptions = {"timezone": "Choose timezone", 
                                    "live_notification": "Live broadcast start notification"
                                    
                                    }



    info_parameter = callback.data.split()[-1]

    text = settings_info_descriptions.get(info_parameter, "Error")

    await bot.answer_callback_query(callback_query_id=callback.id, text=text, show_alert=True)
    CreateLog(callback, 'settings_info', params=info_parameter)


@dp.callback_query_handler(lambda callback: 'settings' in callback.data)
async def settings_change(callback: CallbackQuery):
    
    user_id = callback.message.chat.id
    variable_parameter = callback.data.split()[-1]

    if variable_parameter == 'timezone':
        await callback.message.delete()
        await change_timezone(callback.message)

    elif variable_parameter in ['live_notification']:
        # для булевых значений меняем клавиатуру на ходу
        UPDATE.user_bool_parameter(user_id, variable_parameter)
        await settings(callback.message, edit_message=True)


    

    CreateLog(callback, 'settings_change', params=variable_parameter)




# KEYBOARD ------------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(commands=['keyboard'])
@rate_limit()
async def show_keyboard(message: Message):
    await message.answer(ANSWER_TEXT["keyboard"], reply_markup=REPLY().default())
    CreateLog(message, 'show_keyboard')







# NOT CLICKABLE
@dp.callback_query_handler()
@rate_limit()
async def button_not_clickable(callback: CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback.id, text=ANSWER_CALLBACK["button_not_clickable"])
    CreateLog(callback, 'button_not_clickable')
    #await callback.message.delete()




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



'''
@dp.errors_handler(exception=NetworkError)
async def network_error(update: Update, exception: NetworkError):
    logger.exception_log()
'''



# ADMINS --------------------------------------------------------------------------------------------------------------------------
@dp.message_handler(IDFilter(chat_id=ADMIN_IDS))
async def admin_commands(message: Message):

    message_text_split = message.text.lower().split()
    command = message_text_split[0]

    if command == 'update':
        UpdateData(INSERT, SELECT, message_text_split[1:])
        await message.answer(f"The bot has updated the data about {message_text_split[1:]}")

    elif command == 'get':
        if message_text_split[1] == 'log':
            await bot.send_document(chat_id=message.chat.id, document=open(log_file_local_path, 'rb'))

        elif message_text_split[1] == 'stat':
            print('stat')






# WEBHOOK ------------------------------------------------------------------------------------------------------------------------------
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    await bot.delete_webhook()

    await dp.storage.close()
    await dp.storage.wait_closed()




'''
handlers_functions = [check_new_user, 
                        close, 
                        change_timezone, 
                        selection_timezone, 
                        location, 
                        error_location_selection, 
                        timezone, 
                        error_location_send, 
                        live_matches, 
                        dates_by_match_type,
                        dates,
                        command_with_date,
                        matches_or_results, 
                        matches_by_date, 
                        match_info, 
                        events_type, 
                        events_type_edit, 
                        events_by_type, 
                        event_info, 
                        event_matches, 
                        news, 
                        news_update, 
                        settings, 
                        settings_info, 
                        settings_change, 
                        show_keyboard, 
                        button_not_clickable, 
                        error_bot_blocked]

print(len(handlers_functions))
[print(f.__name__, len(f.__name__)) for f in handlers_functions]
'''


#UpdateData(INSERT, SELECT, ['news'])







def main():
    while True:
        #threading.Thread(target=UpdateData(INSERT, ['matches'])).start()
        
        #dp.middleware.setup(LoggingMiddleware())
        dp.middleware.setup(ThrottlingMiddleware())
        
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