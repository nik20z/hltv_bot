from aiogram import Dispatcher
import aiogram.utils.markdown as fmt
from aiogram.utils.exceptions import BotBlocked

from bot.database import Select
# from bot.config import AnswerText
from bot.keyboards import Inline
from bot.parse import Url


async def live_notifications(dp: Dispatcher):
    """"""
    live_matches = []

    live_matches_info = [x for x in Select.live_matches_for_notice() if x[0] not in live_matches]

    print(f"после перебора live_matches_info {live_matches_info}")

    live_matches = live_matches_info

    print(f"присваиваем live_matches_info к LIVE_MATCHES {live_matches}")

    for match in live_matches_info:

        print(f"match {match}")

        live_matches.remove(match)

        print(f"LIVE_MATCHES после remove {live_matches}")

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

        user_ids = Select.user_ids_for_notice(match_id, team1_id, team2_id, event_id)

        url_match_or_analytics = Url.match_or_analytics('M', match_id, team1_name, team2_name, event_name)

        text = f"{fmt.hide_link(url_match_or_analytics)}"
        # {AnswerText.start_live}"
        keyboard = Inline.notice_start_live(match_obj)

        for user_id in user_ids:
            await dp.bot.send_message(chat_id=user_id,
                                      text=text,
                                      reply_markup=keyboard,
                                      disable_web_page_preview=preview_show)

    print(f"Итого LIVE_MATCHES {live_matches}")


# NEWS NOTIFICATIONS

async def news_notifications(dp: Dispatcher):
    """"""
    user_ids = Select.user_ids_for_news_notice()

    news_object = Select.news(notice=True)

    for one_news in news_object:

        answer_text = get_news_message([one_news])
        if answer_text:
            keyboard = Inline.news(update_button=False)

            for user_id in user_ids:
                try:
                    await dp.bot.send_message(chat_id=user_id,
                                              text=answer_text,
                                              reply_markup=keyboard)
                except BotBlocked:
                    print(f"remove user settings of notification news [{user_id}]")


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
