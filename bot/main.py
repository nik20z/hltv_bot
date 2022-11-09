import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from aiogram.utils import executor
import nest_asyncio

# My Modules
from bot.database import Table
from bot.filters import register_all_filters
from bot.handlers import register_all_handlers
from bot.misc import TgKeys
from bot.functions import get_next_check_time
from bot.functions import update_matches, update_news, update_events
from bot.spamming import live_notifications
from bot.spamming import news_notifications
from bot.throttling import ThrottlingMiddleware


def repeat(func, dp, loop_repeat):
    """Функция-повторитель для loop"""
    asyncio.ensure_future(func(dp), loop=loop_repeat)
    interval = get_next_check_time(func.__name__)
    loop_repeat.call_later(interval, repeat, func, dp, loop_repeat)


async def set_default_commands(dp: Dispatcher) -> None:
    await dp.bot.set_my_commands([
        BotCommand("settings", "settings menu"),
        BotCommand("today", "today's matches"),
        BotCommand("tomorrow", "tomorrow's matches"),
        BotCommand("live", "live broadcasts"),
        BotCommand("events", "events info"),
        BotCommand("results_today", "today's results"),
        BotCommand("news", "latest news"),
        BotCommand("matches", "weekly matches"),
        BotCommand("results", "weekly results"),
        BotCommand("help", "command info"),
        BotCommand("keyboard", "show keyboard")
    ])


async def on_startup(dp: Dispatcher) -> None:
    # await dp.bot.set_webhook(WEBHOOK_URL)
    register_all_filters(dp)
    register_all_handlers(dp)


async def on_shutdown(dp: Dispatcher) -> None:
    # await dp.bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


def start_bot():
    nest_asyncio.apply()

    Table.create()
    Table.create_view()

    bot = Bot(token=TgKeys.TOKEN, parse_mode='HTML')
    dp = Dispatcher(bot, storage=MemoryStorage())

    dp.middleware.setup(LoggingMiddleware())
    dp.middleware.setup(ThrottlingMiddleware())

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(set_default_commands(dp))]
    loop.run_until_complete(asyncio.wait(tasks))

    # loop.call_later(1, repeat, update_events, dp, loop)
    # loop.call_later(1, repeat, update_news, dp, loop)
    # loop.call_later(1, repeat, update_matches, dp, loop)

    # loop.call_later(2, repeat, news_notifications, dp, loop)
    # loop.call_later(2, repeat, live_notifications, dp, loop)

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

    '''
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )'''
