import re
import time
import datetime
import threading

from config import Intervals_parse



def UpdateData_by_timer(INSERT, SELECT, UPDATE, UpdateData):
    threads = []
    for tableName, interval in Intervals_parse.items():
        one_update_thread = threading.Thread(target=UpdateData, 
                            name=tableName, 
                            args=(INSERT, SELECT, UPDATE, [tableName]), 
                            kwargs={'interval': interval})
        one_update_thread.start()



check_message_text = lambda message, commands: message.text.lower().replace('/','') in commands


def check_callback_split(callback, commands: list, ind = -2):
    callback_data_split = callback.data.split()
    try:
        return callback_data_split[ind] in commands
    except:
        return False




def no_except(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            return 
    return wrapper


def time_of_function(func):
    def wrapped(*args, **kwargs):
        start_time = time.perf_counter_ns()
        res = func(*args, **kwargs)
        print(f"{func.__name__} {(time.perf_counter_ns() - start_time)/10**9}")
        return res
    return wrapped



def get_timezone_text(callback_data, interval = False):

    callback_data_split = re.split(':|,', str(callback_data))
    
    hours = int(callback_data_split[-3])
    minutes = int(callback_data_split[-2])

    if 'day' in callback_data_split[0]:
        hours -= 24
    timezone_text = f"{hours+1 if minutes != 0 and hours < 0 else hours}:{minutes}{0 if minutes == 0 else ''}"
    
    if interval:
        timezone = datetime.timedelta(hours=hours, minutes=minutes)
        return timezone_text, timezone
    return timezone_text


def get_date_with_replaces(date_text: str, format_: str, replace_month = None, replace_year = None):
    try:
        date_ = datetime.datetime.strptime(date_text, format_).date()
        
        if not replace_month is None:
            date_ = date_.replace(month=replace_month)
        
        if not replace_year is None:
            date_ = date_.replace(year=replace_year)            

        return date_
    except:
        return 	



def get_correct_date(date_text: str, format_ = "%d.%m.%Y"):
    now_date = datetime.datetime.now().date()
    date_text_split = date_text.split('.')
    
    if len(date_text_split) == 1:
        return get_date_with_replaces(date_text, "%d", replace_month=now_date.month, replace_year=now_date.year)
    
    elif len(date_text_split) == 2:
        return get_date_with_replaces(date_text, "%d.%m", replace_year=now_date.year)
    
    year_text = date_text_split[-1]
    if len(year_text) == 2:
        format_ = "%d.%m.%y"

    return get_date_with_replaces(date_text, format_)




