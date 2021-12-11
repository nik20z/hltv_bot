import os
import re
import asyncio
from loguru import logger

from aiogram.types import Message, CallbackQuery


# можно создать класс для логов, мб потом парсить их\
#logs = open("info.log", "r", encoding="utf-8")



class Parse:

	def __init__(self):
		pass

	def run(self):
		for line in logs:
			print(line)
			line_split = line.replace('[', '|').replace(']', '|').split('|')
			print(line_split)

			for x in line_split:
				print(x.replace(' ', ''))


			break

'''
def CreateLog_decorate(func):
    def wrapper(*args, **kwargs):
        print(*args)
        #print(*kwargs)
        return func(*args)
    return wrapper
'''



def CreateLog(message, command: str, request_type = 'TEXT', params = ''):
    if isinstance(message, CallbackQuery):
        message = message.message
        request_type = 'CALLBACK'

    #print(message)

    user_id = message.chat.id
    chat_type = message.chat.type

    '''
    space_after_chat_type = ' '*(7-len(chat_type))
    space_after_request_type = ' '*(8 - len(request_type))
    space_after_command = ' '*(25 - len(command))
    space_after_params =  ' '*(17 - len(params))

    logger.info(f"[{chat_type.upper()}{space_after_chat_type}] [{request_type}{space_after_request_type}] | {command}{space_after_command}| {params}{space_after_params} | {user_id} |")
    '''

    log_array = [chat_type.upper(), request_type, command, params, user_id]
    
    logger.info(log_array)
