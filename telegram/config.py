GOD_ID = 1020624735
ADMIN_IDS = [GOD_ID, 1475103948]


ANSWER_KEYBOARD = {}



# SMILES

# 🌍 EARTH GLOBE EUROPE-AFRICA
# 🌐


flag_smiles = {'Finland': '🇫🇮',
				'Germany': '🇩🇪',
				'Denmark': '🇩🇰',
				'Norway': '🇳🇴',
				'Ukraine': '🇺🇦',
				'Poland': '🇵🇱',
				'Serbia': '🇷🇸',
				'China': '🇨🇳',
				'Australia': '🇦🇺',
				'Brazil': '🇧🇷',
				'Switzerland': '🇨🇭',
				'United States': '🇺🇸',
				'North America': '🇨🇦 🇺🇸',
				'South America': '🌎',
				'Canada': '🇨🇦',
				'Oceania': '🇳🇿',
				'Sweden': '🇸🇪',
                'Estonia': '🇪🇪',

				'Europe': '🇪🇺',
				'Asia': '🌏'
				}

FLAG_SMILE = lambda location: flag_smiles.get(location.strip(), '🌐')


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
    'dates_text_by_match_type': lambda match_type: "Dates for " + {'R': 'Results', 'U': 'Upcoming matches'}.get(match_type, 'Matches'),
    'correct_date': 'Please enter the correct date\nExamples: \n 🔹 02.06.2002 - full date\n 🔹 2.6 - day and month (current year)\n 🔹 2 - only day (current month and year)',
    'matches_by_type': lambda match_type: {'U': 'Upcoming matches', 'R': 'Results'}.get(match_type, 'Matches'),
    'no_matches_by_type': lambda match_type: {'U': 'Oops .. no matches planned for this day', 'R': 'There are no results for the selected day'}.get(match_type, 'No matches'),
    'match_info': "Match info",
    
    'events_type': "Select the category of events you are interested in",
    'matches_for_event': "Matches for the Event",
    'text_by_event_type': lambda event_type: {'O': 'Ongoing events', 'B': 'Big events', 'S': 'Small events'}[event_type],
    'event_info': "Event information",
    
    'settings': "Settings",
    
    'keyboard': "Keyboard is open"
}

ANSWER_CALLBACK = {
    'no_information_matches':lambda match_type: f"No information about new {'Upcoming matches' if match_type == 'U' else 'Results' if match_type == 'R' else 'matches'}",
    'no_live_broadcasts': "No live broadcasts",
    
    'no_event_data': "No event data",
    
    'news_updated': 'The news feed has been updated 🆕',
    'no_new_news': "No new news appeared",

    'button_not_clickable': "This button is not clickable"
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