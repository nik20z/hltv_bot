GOD_ID = 1020624735
ADMINS = [1020624735]


def notifications_limits(type_notice):
    return {'matches': 35, 'events': 20, 'teams': 35}.get(type_notice, 20)


class ArrayTimes:
    update_events = ("00:05",
                     "23:00",
                     "00:05")

    update_matches = ("00:05",
                      "2:00",
                      "4:00",
                      "6:00",
                      "7:00",
                      "8:00",
                      "9:00",
                      "10:00",
                      "11:00",
                      "12:00",
                      "13:00",
                      "14:00",
                      "15:00",
                      "16:00",
                      "17:00",
                      "18:00",
                      "19:00",
                      "20:00",
                      "21:00",
                      "22:00",
                      "23:00")

    update_news = ("00:05",
                   "6:00",
                   "12:00",
                   "18:00",
                   "23:00")

    news_notifications = update_news
    live_notifications = update_matches


def get_title_event_type(event_type):
    return {'O': "Ongoing", 'B': "Big", 'S': "Small"}.get(event_type, '')


def get_title_match_type(match_type):
    return {'U': "Upcoming matches", 'R': "Results"}.get(match_type, 'matches')


class AnswerText:
    new_user = {
        "welcome_message_private": lambda
            user_name: f'Hello, {user_name} 😊\nI am an HLTV bot, I need to know your time zone to send personalized data\n🔹 Selection timezone - choose from the list yourself\n🔹 Send timezone - send your coordinates',
        "welcome_message_group": lambda
            user_name: f"Greetings to everyone in the group chat <b>{user_name}</b>»\nTo start working with me, you must specify your time zone"
    }
    change_timezone_private = "Choose a method to set your time zone\n🔹 Selection timezone - choose from the list yourself\n🔹 Send timezone - send your coordinates"
    change_timezone_group = "Choose a method to set your time zone\n🔹 Selection timezone - choose from the list yourself"
    selection_timezone = "Choose your time zone"

    location = lambda loc, tz: f"Great, based on your coordinates, a time zone has been selected: {loc} ({tz})"
    error_location_selection = "Wait, you haven't specified timezone yet"
    error_location_send = "Finish with time zone selection"
    timezone = lambda timezone_number: f"Excellent, you chose: UTC {timezone_number}"
    live_matches = "Live matches"
    no_live_matches = "No live broadcasts"
    start_live = "Live broadcast start ⚡"
    dates_text_by_match_type = lambda match_type: "Dates for " + {'R': 'Results', 'U': 'Upcoming matches'}.get(
        match_type, 'Matches')
    correct_date = 'Please enter the correct date\nExamples:\n🔹 02.06.2002 - full date\n🔹 2.6 - day and month (current year)\n🔹 2 - only day (current month and year)'
    matches_by_type = lambda match_type: {'U': 'Upcoming matches', 'R': 'Results'}.get(match_type, 'Matches')
    no_matches_by_type = lambda match_type: {'U': 'Oops .. no matches planned for this day\n Choose another 📄',
                                             'R': 'There are no results for the selected day\n Choose another 📄'
                                             }.get(match_type, 'No matches')
    match_info = "Match info"

    team_info = "Team Info"
    details_by_team = "Details"
    players_by_team = "Players"
    matches_by_team = lambda match_type: get_title_match_type(match_type)
    events_by_team = 'List of Events for the team'

    player_info = "Player Info"

    events_type = "Select the category of events you are interested in"
    matches_for_event = "Matches for the Event"
    text_by_event_type = lambda event_type: get_title_event_type(event_type) + " events"
    events_by_date = lambda date_text: f"Events for {date_text}"
    correct_date_events = "Please enter the correct date\nExamples:\n🔹 01.2022 - month and year\n🔹 1 - only month (current year)"
    no_events_by_date = "There were no events for the selected date"
    event_info = "Event information"

    no_news = 'No news for the selected day'

    settings = "Settings"

    notifications = "Notification subscriptions"

    search_type_correct = "Please enter the correct search type:\n🔹 team {team_name}\n🔹 player {player_name}"
    search_results = lambda name_search: f"Team search results by query «{name_search}»"
    search_enter_correct = lambda type_search: f"Enter the correct {type_search} name"
    search_not_found = lambda type_search: f"No {type_search} found with the given name"
    help = """
This is what I can do:

/settings - settings menu
/today - today's matches
/tomorrow - tomorrow's matches
/live - live broadcasts
/results_today - today's results
/events - events information
/news - latest news
/matches - weekly matches
/results - weekly results
/keyboard - show keyboard

/notifications - list of notification subscriptions

Date picker:
mathces {date} - matches for a specific day
results {date} - results
news {date} - news

search team {team_name} - team search
search player {player_name} - player search
"""

    keyboard = "Keyboard is open"

    filter_info = lambda info_d: create_filter_info(info_d)

    other_messages = ("other_messages", "other_messages")

    show_keyboard = "Add keyboard"


def create_filter_info(info_d):
    message = '\nFilter: '
    for param, value in info_d.items():
        if param == 'stars':
            message += 'ALL stars' if not value else '⭐' * value + '\n'

        # other parameters

    return message


class AnswerCallback:
    no_dates = "No upcoming matches are planned"
    no_information_matches = lambda match_type: "No information about new " + get_title_match_type(match_type)
    no_matches_by_type = lambda match_type: "No information about " + get_title_match_type(match_type)
    no_live_broadcasts = "No live broadcasts"

    no_events_by_type = lambda event_type: "There are no " + get_title_event_type(event_type) + " events"
    no_events_by_team = "The team does not participate in Events"
    no_event_data = "No event data"
    no_event_matches = "No information about matches"

    news_updated = 'The news feed has been updated 🆕'
    no_new_news = "No new news appeared"

    button_not_clickable = "This button is not clickable"

    notice_info_by_type = lambda type_notice: {
        'teams': 'Teams list\nYou can find the team with the query: search team {team_name}',
        'matches': 'Matches list',
        'events': 'Events list'}.get(type_notice, 'List of subscriptions')

    notice_deleted = "Notification removed"
    notice_by_type = lambda type_notive: {'matches': "Match start notification",
                                          'events': "Matches Notification for Event",
                                          'teams': "Matches Notification for Team"
                                          }.get(type_notive, 'Notification set')
    notice_limit = lambda type_notice, limit: f"Can't add more {limit} {type_notice}"

    no_team_data = "No data available for this team"
    no_player_data = "No data available for this player"

    no_players_by_team = "No players data"


Info_Buttons_Description = {'timezone': "Choose timezone",
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
