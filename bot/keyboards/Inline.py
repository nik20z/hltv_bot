from aiogram.types import InlineKeyboardMarkup
from datetime import datetime, timedelta

from bot.parse import Url
from bot.parse.config import get_season_smile

from .util import add_in_text, format_date
from .util import Button
from .util import get_back_button
from .util import get_close_button
from .util import get_event_button
from .util import get_match_button
from .util import get_player_button
from .util import get_subscribe_button
from .util import get_smile_condition
from .util import get_team_button
from .util import get_timezone_text
from .util import get_update_button


# from bot.misc import Donate
# from bot.misc import Communicate


def news(row_width=2, update_button=True):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    buttons = [get_close_button()]
    if update_button:
        buttons.append(get_update_button("news_update"))

    keyboard.add(*buttons)
    return keyboard


def get_string_buttons(buttons_info: dict):
    buttons = []
    for text, value in buttons_info.items():
        buttons.append(Button(text).inline(value))
    return buttons


def settings(user_settings_info: tuple, row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)

    timezone = user_settings_info[0]
    receive_notices = user_settings_info[1]
    news_notice = user_settings_info[2]
    delete_old_matches = user_settings_info[3]
    delete_old_events = user_settings_info[4]
    stars_matches_display = user_settings_info[5]

    # TIMEZONE
    text_value = get_timezone_text(timezone)
    keyboard.add(*get_string_buttons({'Timezone': "info_button timezone",
                                      text_value: "settings_change timezone"}))

    # NOTIFICATIONS SETTINGS
    keyboard.add(*get_string_buttons({'Notifications': "info_button notifications",
                                      '▶': "s n"}))

    # RECEIVE NOTICES
    text_value = get_smile_condition(receive_notices)
    keyboard.add(*get_string_buttons({'Receive notices': "info_button receive_notices",
                                      text_value: "settings_change receive_notices"}))

    # NOTICE_NEWS
    text_value = get_smile_condition(news_notice)
    keyboard.add(*get_string_buttons({'News notice': "info_button news_notice",
                                      text_value: "settings_change news_notice"}))

    # DELETE MATCHES
    text_value = get_smile_condition(delete_old_matches)
    keyboard.add(*get_string_buttons({'Delete matches': "info_button delete_old_matches",
                                      text_value: "settings_change delete_old_matches"}))

    # DELETE EVENTS
    text_value = get_smile_condition(delete_old_events)
    keyboard.add(*get_string_buttons({'Delete events': "info_button delete_old_events",
                                      text_value: "settings_change delete_old_events"}))

    #
    # stars_matches_display
    keyboard.add(*get_string_buttons({'Stars display': "info_button stars_matches_display",
                                      'ALL' if not stars_matches_display else '⭐' * stars_matches_display: "settings_change stars_matches_display"}))

    keyboard.add(get_close_button())

    return keyboard


def notice_start_live(match_obj, row_width=1, last_callback_data='nsl'):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    match_id = match_obj[0]
    team1_name = match_obj[3]
    team2_name = match_obj[4]
    event_id = match_obj[5]
    event_name = match_obj[6]

    url_live = Url.live_broadcast(match_id)
    url_event = Url.event(event_id, event_name)

    keyboard.add(
        Button(f"{team1_name} vs {team2_name}").inline(f"{last_callback_data} mi {match_id}", url=url_live))
    keyboard.add(Button(event_name).inline(f"{last_callback_data} ei {event_id}", url=url_event))

    return keyboard


def matches(matches_array: list,
            last_callback_data: str,
            row_width=2,
            date_=False,
            add_url=False,
            url=None,
            add_live_mark=False, ):
    """"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    if date_:
        match_type = last_callback_data.split()[1]
        button_text = format_date(date_)
        keyboard.add(Button(button_text).inline(f"d {match_type}"))

    for match in matches_array:
        match_btn = get_match_button(match,
                                     last_callback_data,
                                     add_live_mark=add_live_mark,
                                     add_url=add_url)
        keyboard.add(match_btn)

    if 'ei' in last_callback_data:
        keyboard.add(get_back_button(last_callback_data, offset=-1))
    else:
        keyboard.add(get_close_button(), get_update_button(last_callback_data))

    return keyboard


def match_info(obj: tuple,
               last_callback_data: str,
               subscription: bool,
               row_width=3,
               team1_url=None,
               team2_url=None,
               event_url=None):
    keyboard = InlineKeyboardMarkup(row_width=row_width)

    match_id = obj[0]
    match_type = obj[1]
    date_time_char = obj[2]
    stars = obj[3]
    meta = obj[4]
    team1_id = obj[5]
    team1_name = obj[6]
    team2_id = obj[7]
    team2_name = obj[8]
    event_id = obj[9]
    event_name = obj[10]
    result_score = obj[11]

    last_callback_data_split = last_callback_data.split()

    # TEXT AND URL
    stars_meta_text = f"{'⭐' * stars} {'bo' if meta.isdigit() else ''}{meta}"

    url_match = Url.match_or_analytics('M', match_id, team1_name, team2_name, event_name)
    url_analytics = Url.match_or_analytics('A', match_id, team1_name, team2_name, event_name)

    # CALLBACK_DATA
    team1_info = f"{last_callback_data} ti {team1_id}"
    team2_info = f"{last_callback_data} ti {team2_id}"

    callback_data = ' '.join(last_callback_data.split()[:-2])

    if 'ei' not in last_callback_data:
        callback_data = f"{last_callback_data} ei {event_id}"

    # если до этого открывали матчи для ивента или матчи/результаты для команды
    if 'em' in last_callback_data_split or 'um' in last_callback_data_split or 'rm' in last_callback_data_split:
        team1_url = Url.team(team1_id, team1_name)
        team2_url = Url.team(team2_id, team2_name)

    # если до этого открывали матчи/результаты для команды
    if 'um' in last_callback_data_split or 'rm' in last_callback_data_split:
        event_url = Url.event(event_id, event_name)

    # BUTTONS
    button_team1_name = Button(team1_name).inline(team1_info, url=team1_url)
    button_team2_name = Button(team2_name).inline(team2_info, url=team2_url)
    button_time = Button(date_time_char).inline(f"look_info {date_time_char}")
    button_stars_meta = Button(stars_meta_text).inline(f"look_info {stars_meta_text}")
    button_event_name = Button(event_name).inline(callback_data, url=event_url)
    button_match_info = Button('Match info').inline('match_info_url', url=url_match)
    button_analytics = Button('Analytics').inline('analytics_url', url=url_analytics)
    button_back = get_back_button(last_callback_data)
    button_subscribe = get_subscribe_button(subscription, last_callback_data)

    # ADD BUTTONS
    buttons_first_string = [button_team1_name, button_team2_name]
    buttons_second_string = [button_time, button_stars_meta]

    if match_type == 'R':
        res_team1 = result_score[0]
        res_team2 = result_score[-1]

        result_text = f"{res_team1} - {res_team2}"

        if res_team1 > res_team2:
            result_text = '🟢 ' + result_text + ' 🔴'
        else:
            result_text = '🔴 ' + result_text + ' 🟢'

        button_result_score = Button(result_text).inline(f"look_info {result_text}")
        buttons_first_string.insert(1, button_result_score)

    keyboard.add(*buttons_first_string)
    keyboard.add(*buttons_second_string)
    keyboard.add(button_event_name)
    keyboard.add(button_match_info, button_analytics)
    keyboard.add(button_back, button_subscribe)

    return keyboard


def matches_by_team_id(matches_array: tuple,
                       last_callback_data: str,
                       row_width=1,
                       add_live_mark=True):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    for match in matches_array:
        match_btn = get_match_button(match,
                                     last_callback_data,
                                     add_time=True,
                                     add_live_mark=add_live_mark,
                                     add_url=False)
        keyboard.add(match_btn)

    keyboard.add(get_back_button(last_callback_data))

    return keyboard


def notifications(d: dict,
                  last_callback_data: str,
                  row_width=1,
                  add_back_button=False,
                  add_close_button=True,
                  add_team_flag=True):
    """"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    texts = {'teams': '🌀 Teams 🌀',
             'matches': '🆚 Matches 🆚',
             'events': '🎯 Events 🎯'
             }

    for notice_type, obj in d.items():
        print("obj", obj)

        text_button_notice_type = texts[notice_type]
        keyboard.add(Button(text_button_notice_type).inline(f"notice_info {notice_type}"))

        for x in obj:

            if notice_type == 'teams':
                keyboard.add(get_team_button(x, last_callback_data, add_flag=add_team_flag))

            elif notice_type == 'matches':
                keyboard.add(get_match_button(x, last_callback_data, add_time=True, add_live_mark=True))

            elif notice_type == 'events':
                keyboard.add(get_event_button(x, last_callback_data))

    if last_callback_data is not None and 's' in last_callback_data.split():
        add_back_button = True
        add_close_button = False

    last_row_buttons = []

    if add_back_button:
        last_row_buttons.append(get_back_button(last_callback_data, offset=-1))

    if add_close_button:
        last_row_buttons.append(get_close_button())

    keyboard.add(*last_row_buttons)

    return keyboard


def teams_list(all_teams_obj: tuple,
               last_callback_data: str,
               row_width=1,
               add_flag=False,
               columns=1,
               rows=4,
               max_columns=3):
    """"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    for team_obj in all_teams_obj:
        keyboard.add(get_team_button(team_obj, last_callback_data, add_flag=add_flag))

    keyboard.add(get_close_button())

    return keyboard


def players_list(all_players_obj: tuple,
                 last_callback_data: str,
                 row_width=1,
                 add_close_button=True,
                 return_keyboard=False,
                 add_flag=True,
                 columns=1,
                 rows=4,
                 max_columns=3):
    # ВЫНЕСТИ В ОТДЕЛЬНУЮ ФУНКЦИЮ
    def get_array_by_count_colomn(array, n):
        return [array[i:i + n] for i in range(0, len(array), n)]

    columns_first_count = len(all_players_obj) // rows + 1
    columns = max_columns if columns_first_count > max_columns else columns_first_count

    all_players_obj_sorted = get_array_by_count_colomn(all_players_obj, columns)

    players_string = []
    for players_string_obj in all_players_obj_sorted:
        for player_obj in players_string_obj:
            players_string.append(get_player_button(player_obj, last_callback_data, add_flag=add_flag))

    if return_keyboard:
        keyboard = InlineKeyboardMarkup(row_width=row_width)
        keyboard.add(*players_string)
        if add_close_button:
            keyboard.add(get_close_button())
        return keyboard

    return players_string

def team_info(obj: tuple,
              last_callback_data: str,
              subscription: bool,
              row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    team_id = obj[0]
    team_name = obj[1]
    flag = obj[2]

    # TEXT AND URL
    url_team = Url.team(team_id, team_name)

    # BUTTONS
    button_team_name = Button(add_in_text(team_name, flag)).inline(team_id, url=url_team)
    button_details = Button("Details").inline(f"{last_callback_data} dt {team_id}")
    button_players = Button("Players").inline(f"{last_callback_data} pt {team_id}")
    button_upcoming_matches = Button("Upcoming matches").inline(f"{last_callback_data} um {team_id}")
    button_results_matches = Button("Results of matches").inline(f"{last_callback_data} rm {team_id}")
    button_events = Button("Events").inline(f"{last_callback_data} etm {team_id}")
    button_back = get_back_button(last_callback_data)
    button_subscribe = get_subscribe_button(subscription, last_callback_data)

    # ADD BUTTONS
    keyboard.add(button_team_name)
    keyboard.add(button_details, button_players)
    keyboard.add(button_upcoming_matches)
    keyboard.add(button_results_matches)
    keyboard.add(button_events)
    keyboard.add(button_back, button_subscribe)

    return keyboard


def player_info(obj: tuple,
                last_callback_data: str,
                row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    player_id = obj[0]
    team_id = obj[1]
    team_name = obj[2]
    team_flag = obj[3]
    player_nik_name = obj[4]
    # player_name = obj[5]
    flag = obj[6]
    number_maps = obj[7]
    number_rounds = obj[8]
    kd_diff = obj[9]
    kd = obj[10]
    rating_1_0 = obj[11]

    # TEXT AND URL
    player_nik_name_text = add_in_text(player_nik_name, flag)
    team_name_text = f" Team: {add_in_text(team_name, team_flag)}"

    url_player = Url.player(player_id, player_nik_name)
    url_team = Url.team(team_id, team_name)

    # CALLBACK_DATA
    callback_team_info = f"{last_callback_data} ti {team_id}"

    # BUTTONS
    button_player_nik_name = Button(player_nik_name_text).inline(player_id, url=url_player)
    # button_player_name = Button(player_name).inline(player_id, url=url_player)
    button_team_name = Button(team_name_text).inline(callback_team_info)

    if 'pt' in last_callback_data.split():
        button_team_name = Button(team_name_text).inline(team_id, url=url_team)

    button_back = get_back_button(last_callback_data)

    # ADD BUTTONS
    keyboard.add(button_player_nik_name)  # , button_player_name)
    keyboard.add(button_team_name)

    keyboard.add(*get_string_buttons({'Maps': "info_button number_maps",
                                      number_maps: f"look_info {number_maps}"}))

    keyboard.add(*get_string_buttons({'Rounds': "info_button number_rounds",
                                      number_rounds: f"look_info {number_rounds}"}))

    kd_diff_text = f"{kd_diff} {'🔻' if kd_diff < 0 else '🆙'}"
    keyboard.add(*get_string_buttons({'K-D Diff': "info_button kd_diff",
                                      kd_diff_text: f"look_info {kd_diff_text}"}))

    keyboard.add(*get_string_buttons({'K/D': "info_button kd",
                                      kd: f"look_info {kd}"}))

    keyboard.add(*get_string_buttons({'Rating 1.0': "info_button rating_1_0",
                                      rating_1_0: f"look_info {rating_1_0}"}))

    keyboard.add(button_back)

    return keyboard


def details_by_team(details: tuple,
                    last_callback_data: str,
                    row_width=2):
    """"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    team_id = details[0]
    team_name = details[1]
    flag = details[2]
    number_maps = details[3]
    kd_diff = details[4]
    kd = details[5]
    rating = details[6]

    # TEXT
    team_name_text = add_in_text(team_name, flag)
    url_team = Url.team(team_id, team_name)

    # BUTTONS
    button_team_name = Button(team_name_text).inline(team_id, url=url_team)
    button_back = get_back_button(last_callback_data)

    # ADD BUTTONS
    keyboard.add(button_team_name)

    keyboard.add(*get_string_buttons({'Maps': "info_button number_maps",
                                      number_maps: f"look_info {number_maps}"}))

    kd_diff_text = f"{kd_diff} {'🔻' if kd_diff is None or kd_diff < 0 else '🆙'}"
    keyboard.add(*get_string_buttons({'K-D Diff': "info_button kd_diff",
                                      kd_diff_text: f"look_info {kd_diff_text}"}))

    keyboard.add(*get_string_buttons({'K/D': "info_button kd",
                                      kd: f"look_info {kd}"}))

    keyboard.add(*get_string_buttons({'Rating 1.0': "info_button rating",
                                      rating: f"look_info {rating}"}))

    keyboard.add(button_back)

    return keyboard


def players_by_team(players_info: tuple,
                    last_callback_data: str,
                    add_flag=True,
                    row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)

    team_id = players_info[0][-3]
    team_name = players_info[0][-2]
    team_flag = players_info[0][-1]

    # TEXT AND URL
    team_name_text = add_in_text(team_name, team_flag)

    url_team = Url.team(team_id, team_name)

    # BUTTONS
    button_team_name = Button(team_name_text).inline(team_id, url=url_team)
    button_back = get_back_button(last_callback_data)

    # ADD BUTTONS
    keyboard.add(button_team_name)
    keyboard.add(*players_list(players_info, last_callback_data, add_close_button=False, add_flag=add_flag))
    keyboard.add(button_back)

    return keyboard


def timezones(row_width=2):
    """"""
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    # config
    timezones_array_minus = (
        '12:00', '11:00', '10:00', '9:30', '9:00', '8:00', '7:00', '6:00', '5:00', '4:00', '3:30', '3:00', '2:00',
        '1:00')
    timezones_array_plus = (
        '0:00', '1:00', '2:00', '3:00', '3:30', '4:00', '4:30', '5:00', '5:30', '5:45', '6:00', '6:30', '7:00',
        '8:00',
        '8:45', '9:00', '10', '10:30', '11:00', '12:00', '12:45', '13:00', '14:00')

    buttons_minus = [
        Button(f"UTC−{x}").inline(str(timedelta(hours=-int(x.split(':')[0]), minutes=-int(x.split(':')[-1]))))
        for x in timezones_array_minus]
    buttons_plus = [
        Button(f"UTC+{x}").inline(str(timedelta(hours=int(x.split(':')[0]), minutes=int(x.split(':')[-1])))) for
        x in timezones_array_plus]

    keyboard.add(*buttons_minus, *buttons_plus)

    return keyboard


def dates(match_type: str, dates_array: list, row_width=1):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    for date_ in dates_array:
        button_text = format_date(date_[0])
        keyboard.add(Button(button_text).inline(f"d {match_type} m {date_[0]}"))

    keyboard.add(get_close_button())

    return keyboard


def events_type(row_width=1):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    buttons = []
    events_type_dict = {'O': "Ongoing events",
                        'B': "Big events",
                        'S': "Small events"}

    for events_type, text in events_type_dict.items():
        btn = Button(text).inline(f"et ebt {events_type}")
        buttons.append(btn)

    keyboard.add(*buttons)
    keyboard.add(get_close_button())
    return keyboard


def events(event_type: str,
           events_array: list,
           last_callback_data: str,
           add_months=True,
           add_url=False,
           add_back_button=True,
           add_close_button=False,
           url=None,
           row_width=2):
    keyboard = InlineKeyboardMarkup(row_width=row_width)
    last_month = ''
    for event in events_array:
        event_id = event[0]
        event_name = event[1]
        start_date = event[2]

        month = start_date.strftime("%B")
        if add_months and event_type != 'O' and month != last_month:
            smile = get_season_smile(month)
            month_text = f"{smile} {month} {smile}"
            keyboard.add(Button(month_text).inline(f"look_info {month_text}"))
            last_month = month

        if add_url:
            url = Url.event(event_id, event_name)

        button_event = Button(event_name).inline(f"{last_callback_data} ei {event_id}", url=url)
        keyboard.add(button_event)

    if add_back_button:
        keyboard.add(get_back_button(last_callback_data))
    else:
        keyboard.add(get_close_button())

    return keyboard


def events_by_team(events_array: list, last_callback_data: str):
    return events("", events_array, last_callback_data, add_months=False, add_url=True)


def events_by_date(events_array: list, last_callback_data: str):
    return events("", events_array, last_callback_data, add_back_button=False)


def event_info(obj: tuple,
               last_callback_data: str,
               subscription: bool,
               row_width=3):
    def get_date_text(date_):
        date_convert = datetime.strftime(date_, '%b %#d')
        days = str(date_.day)
        try:
            if days[0] == '1':
                raise Exception
            ending = {'1': 'st', '2': 'nd', '3': 'rd'}[days[-1]]
        except Exception:
            ending = 'th'
        return f"{date_convert}{ending}"

    keyboard = InlineKeyboardMarkup(row_width=row_width)

    event_id = obj[0]
    # event_type = obj[1]
    event_name = obj[2]
    event_location = obj[3]
    flag = obj[4]
    start_date = get_date_text(obj[5])
    stop_date = get_date_text(obj[6])
    prize = obj[7]
    count_teams = obj[8]

    # TEXT
    url_event = Url.event(event_id, event_name)
    location_text = f"{flag} {event_location}"
    dates_text = f"{start_date} — {stop_date}"
    prize_text = f"Prize: {'' if prize is None else '💲'}{prize if prize is None else '{:,}'.format(prize)}"
    teams_text = f"Teams: {count_teams}"

    # CALLBACK DATA
    callback_data = f"{last_callback_data} em"

    # ADD BUTTONS
    button_event_name = Button(event_name).inline("event_name", url=url_event)
    button_location = Button(location_text).inline(f"look_info {location_text}")
    button_date = Button(dates_text).inline(f"look_info {dates_text}")
    button_prize = Button(prize_text).inline(f"look_info {prize_text}")
    button_teams = Button(teams_text).inline(f"look_info {teams_text}")
    button_matches = Button("All Matches").inline(callback_data)
    button_back = get_back_button(last_callback_data)
    button_subscribe = get_subscribe_button(subscription, last_callback_data)

    keyboard.add(button_event_name)
    keyboard.add(button_location, button_date)
    keyboard.add(button_prize, button_teams)
    keyboard.add(button_matches)
    keyboard.add(button_back, button_subscribe)

    return keyboard
