from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.dispatcher.filters import IDFilter

import requests
import sys
import time

from bot.config import ADMINS
from bot.parse import handler_parse


async def update(message: Message):
    """"""
    t = time.time()
    args_split = message.get_args().split()

    all_updates = ['matches', 'news', 'events', 'stats_teams', 'stats_players']
    type_updates = [up for up in args_split if up in all_updates]

    session = requests.Session()
    p = handler_parse.HandlerParse(session=session)

    for type_upd in type_updates:

        if type_upd == "matches":
            p.upcoming_and_live()
            p.results()

        elif type_upd == "news":
            p.news()

        elif type_upd == "events":
            p.events()

        elif type_upd == "stats_teams":
            p.stats_teams()

        elif type_upd == "stats_players":
            p.stats_players()

    session.close()

    text = 'Enter the correct command'
    if len(type_updates) != 0:
        text = f"The bot has updated the data about {type_updates} in {round(time.time() - t, 1)} seconds"

    await message.answer(text)


async def info_log(message: Message):
    """Получаем log-файл"""
    user_id = message.chat.id
    await message.bot.send_document(user_id, open("bot/log/info.log"))


async def restart_bot(message: Message):
    """Перезапускаем бота"""
    await message.answer("restart_bot")
    sys.exit()


def register_admin_handlers(dp: Dispatcher):
    # todo: register all admin handlers

    dp.register_message_handler(update,
                                IDFilter(chat_id=ADMINS),
                                commands=['update'])

    dp.register_message_handler(info_log,
                                IDFilter(chat_id=ADMINS),
                                commands=['info_log'])

    dp.register_message_handler(restart_bot,
                                IDFilter(chat_id=ADMINS),
                                commands=['restart_bot'])
