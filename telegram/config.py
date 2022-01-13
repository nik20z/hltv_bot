GOD_ID = 1020624735
ADMIN_IDS = [GOD_ID]


ANSWER_KEYBOARD = {}


notifications_limits = lambda type_notice: {'matches': 35, 'events': 20, 'teams': 35}.get(type_notice, 20)


# SMILES
# 🌐
# Jordan
# Montenegro


flag_smiles = {'Albania': '🇦🇱',
    'Argentina': '🇦🇷',
    'Asia': '🌏',
    'Australia': '🇦🇺',
    'Austria': '🇦🇹',
    'Azerbaijan': '',
    'Belgium': '🇧🇪',
    'Belarus': '🇧🇾',
    'Bosnia and Herzegovina': '🇧🇦',
    'Brazil': '🇧🇷',
    'Bulgaria': '🇧🇬',
    'Canada': '🇨🇦',
    'China': '🇨🇳',
    'CIS': 'CIS',
    'Cyprus': '🇨🇾',
    'Czech Republic': '🇨🇿',             
    'Denmark': '🇩🇰',
    'Estonia': '🇪🇪',
    'Europe': '🇪🇺',
    'Finland': '🇫🇮',
    'France': '🇫🇷',
	'Germany': '🇩🇪',
    'Guatemala': '🇬🇹',
    'Hong Kong': '🇭🇰',
    'Hungary': '🇭🇺',
    'Iceland': '🇮🇸',
    'Indonesia': '🇮🇩',
    'Ireland': '🇮🇪',
    'Israel': '🇮🇱',
    'Italy': '🇮🇹',
    'Japan': '🇯🇵',
    'Korea': '🇰🇷',
    'Kazakhstan': '🇰🇿',
    'Lithuania': '🇱🇹',
    'Latvia': '🇱🇻',
    'Macedonia': '🇲🇰',
    'Malaysia': '🇲🇾',
    'Malta': '🇲🇹',
    'Mexico': '🇲🇽',
    'Mongolia': '🇲🇳',
	'Netherlands': '🇳🇱',
    'New Zealand': '🇳🇿',
	'North America': '🇨🇦 🇺🇸',
    'Norway': '🇳🇴',				
    'Oceania': '🇳🇿',
	'Poland': '🇵🇱',
    'Portugal': '🇵🇹',
    'Romania': '🇷🇴',
    'Russia': '🇷🇺',
    'Singapore': '🇸🇬',
    'Slovakia': '🇸🇰',
    'South Africa': '🌍',
    'South America': '🌎',
	'Serbia': '🇷🇸',
    'Spain': '🇪🇸',
    'Sweden': '🇸🇪',
    'Switzerland': '🇨🇭',
    'Taiwan': '🇹🇼',
    'Thailand': '🇹🇭',
    'Turkey': '🇹🇷',
	'Ukraine': '🇺🇦',
    'United Kingdom': '🇬🇧',
	'United States': '🇺🇸',
    'Uruguay': '🇺🇾',
    'Uzbekistan': '🇺🇿'
}


#🍂
seasons_smile = {
    'January': '🎄',
    'February': '❄',
    'March': '☀',
    'April': '☀',
    'May': '☀',
    'June': '🌳',
    'July': '🌳',
    'August': '🌳',
    'September': '🍁',
    'October': '🍁',
    'November': '🍁',
    'December': '⛄',
}




FLAG_SMILE = lambda location: flag_smiles.get(location.strip(), '🌐')

SEASSONS_SMILE = lambda seasson: seasons_smile.get(seasson, '')




get_title_event_type = lambda event_type: {'O': "Ongoing", 'B': "Big", 'S': "Small"}.get(event_type, '')
get_title_match_type = lambda match_type: {'U': "Upcoming matches", 'R': "Results"}.get(match_type, 'matches')



# ANSWERS

ANSWER_TEXT = {
    'welcome_message_private': lambda name: f"Hello, {name} 😊\nI am an HLTV bot, I need to know your time zone to send personalized data\n 🔹 Selection timezone - choose from the list yourself\n 🔹 Send timezone - send your coordinates",  
    'welcome_message_group': lambda name: f"Greetings to everyone in the group chat <b>{name}</b>»\nTo start working with me, you must specify your time zone",

    'change_timezone_private': "Choose a method to set your time zone\n 🔹 Selection timezone - choose from the list yourself\n 🔹 Send timezone - send your coordinates",
    'change_timezone_group': "Choose a method to set your time zone\n 🔹 Selection timezone - choose from the list yourself",
    'selection_timezone': "Choose your time zone",
    'location': lambda location, timezone: f"Great, based on your coordinates, a time zone has been selected: {location} ({timezone})",
    'error_location_selection': "Wait, you haven't specified timezone yet",
    'error_location_send': "Finish with time zone selection",
    'timezone': lambda timezone_number: f"Excellent, you chose: UTC {timezone_number}",
    
    'live_matches': "Live matches",
    'no_live_matches': "No live broadcasts",
    'start_live': "Live broadcast start ⚡",
    'dates_text_by_match_type': lambda match_type: "Dates for " + {'R': 'Results', 'U': 'Upcoming matches'}.get(match_type, 'Matches'),
    'correct_date': 'Please enter the correct date\nExamples: \n 🔹 02.06.2002 - full date\n 🔹 2.6 - day and month (current year)\n 🔹 2 - only day (current month and year)',
    'matches_by_type': lambda match_type: {'U': 'Upcoming matches', 'R': 'Results'}.get(match_type, 'Matches'),
    'no_matches_by_type': lambda match_type: {'U': 'Oops .. no matches planned for this day\nChoose another 📄', 'R': 'There are no results for the selected day\nChoose another 📄'}.get(match_type, 'No matches'),
    'match_info': "Match info",

    'team_info': "Team Info",
    'details_by_team': "Details",
    'matches_by_team': lambda match_type: get_title_match_type(match_type),
    'events_by_team': 'List of Events for the team',

    'player_info': "Player Info",
    
    'events_type': "Select the category of events you are interested in",
    'matches_for_event': "Matches for the Event",
    'text_by_event_type': lambda event_type: get_title_event_type(event_type) + " events",
    'events_by_date': lambda date_text: f"Events for {date_text}",
    'correct_date_events': "Please enter the correct date\nExamples: \n 🔹 01.2022 - month and year \n 🔹 1 - only month (current year)",
    'no_events_by_date': "There were no events for the selected date",
    'event_info': "Event information",

    'no_news': 'No news for the selected day',
    
    'settings': "Settings",
    
    'notifications': "Notification subscriptions",
    
    'search_type_correct': "Please enter the correct search type:\n 🔹 team {team_name}\n 🔹 player {player_name}",
    'search_results': lambda name_search: f"Team search results by query «{name_search}»",
    'search_enter_correct': lambda type_search: f"Enter the correct {type_search} name",
    'search_not_found': lambda type_search: f"No {type_search} found with the given name",
    'help': 
"""
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
""",
    
    'keyboard': "Keyboard is open",

    'filter_info': lambda info_d: create_filter_info(info_d)
}


def create_filter_info(info_d):
    message = '\nFilter: '
    for param, value in info_d.items():
        if param == 'stars':
            message += 'ALL stars' if not value else '⭐'*value + '\n'

        # other parameters

    return message


ANSWER_CALLBACK = {
	'no_dates': "No upcoming matches are planned",
    'no_information_matches':lambda match_type: "No information about new " + get_title_match_type(match_type),
    'no_matches_by_type': lambda match_type: "No information about " + get_title_match_type(match_type),
    'no_live_broadcasts': "No live broadcasts",
    
    'no_events_by_type': lambda event_type: "There are no " + get_title_event_type(event_type) + " events",
    'no_events_by_team': "The team does not participate in Events",
    'no_event_data': "No event data",
    'no_event_matches': "No information about matches",
    
    'news_updated': 'The news feed has been updated 🆕',
    'no_new_news': "No new news appeared",

    'button_not_clickable': "This button is not clickable",

    'notice_info_by_type': lambda type_notice: {'teams': 'Teams list\nYou can find the team with the query: search team {team_name}', 
                                                'matches': 'Matches list', 
                                                'events': 'Events list'}.get(type_notice, 'List of subscriptions'),

    'notice_deleted': "Notification removed",
    'notice_by_type': lambda type_notive: {'matches': "Match start notification",
                                            'events': "Matches Notification for Event",
                                            'teams': "Matches Notification for Team"
                                            }.get(type_notive, 'Notification set'),
    'notice_limit': lambda type_notice, limit: f"Can't add more {limit} {type_notice}",

    'no_team_data': "No data available for this team",
    'no_player_data': "No data available for this player"
}


# ANTIFLOOD

rate_limit_default = 5

RATE_LIMITS = {
                'close':                        5,
                'change_timezone':              5,
                'selection_timezone':           5,
                'location':                     5,
                'error_location_selection':     5,
                'timezone':                     4,
                'error_location_send':          5,
                'live_matches':                 5,
                'dates_by_match_type':          5,
                'dates':                        5,
                'command_with_date':            5,
                'matches_or_results':           5,
                'matches_by_date':              5,
                'match_info':                   5,
                'events_type':                  5,
                'events_type_edit':             5,
                'events_by_type':               5,
                'event_info':                   5,
                'event_matches':                5,
                'news':                         5,
                'news_update':                  5,
                'settings':                     5,
                'settings_info':                5,
                'settings_change':              5,
                'show_keyboard':                5,
                'button_not_clickable':         5, 
                'error_bot_blocked':            5 

}