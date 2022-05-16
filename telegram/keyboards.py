import datetime
import re

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.types import KeyboardButton, InlineKeyboardButton

from functions import get_timezone_text
from data.config import MAIN_URL

from telegram.config import SEASSONS_SMILE


format_date = lambda date_: datetime.datetime.strftime(date_, '%#d %b (%A)')



class URL:

	def news(self, id_: int, href: str):
		return f"{MAIN_URL}news/{id_}/{href}"

	def join_hyphen(self, text: str):
		if text != None:
			return '-'.join(text.lower().split())

	def event(self, event_id: int, event_name: str):
		return f"{MAIN_URL}events/{event_id}/{self.join_hyphen(event_name)}"

	def match_or_analytics(self, type_: str, match_id: int, team1_name: str, team2_name: str, event_name: str):
		try:
			type_text = {'M': 'matches/', 'A': 'betting/analytics/'}[type_]
			return f"{MAIN_URL}{type_text}{match_id}/{self.join_hyphen(team1_name)}-vs-{self.join_hyphen(team2_name)}-{self.join_hyphen(event_name)}"
		except:
			return MAIN_URL

	def live_broadcast(self, match_id: int):
		return f"{MAIN_URL}live?=matchId{match_id}"

	def team(self, team_id: int, team_name: str):
		return f"{MAIN_URL}team/{team_id}/{self.join_hyphen(team_name)}"

	def player(self, player_id: int, player_nik_name: str):
		return f"{MAIN_URL}player/{player_id}/{self.join_hyphen(player_nik_name)}"



class BUTTON:
    def __init__(self, text: str):
        self.text = str(text)

    def inline(self, callback_data: str, url = None):
        return InlineKeyboardButton(text=self.text, 
                                    callback_data=str(callback_data), 
                                    url=url)

    def reply(self, request_location = False):
        return KeyboardButton(text=self.text, 
                                request_location=request_location)


class REPLY:
	def __init__(self, row_width = 3):
		self.keyboard = ReplyKeyboardMarkup(row_width=row_width, resize_keyboard=True)

	def default(self):
		self.keyboard.add('Today', 'Tomorrow', 'Live')
		self.keyboard.add('Events', 'Results today')
		return self.keyboard

	def location(self, send_location_button = False):
		self.keyboard.add(BUTTON("Selection timezone 📋").reply())
		if send_location_button:
			self.keyboard.add(BUTTON("Send location 🗺").reply(request_location=True))
		return self.keyboard



class INLINE:

	def __init__(self, row_width = 3):
		self.keyboard = InlineKeyboardMarkup(row_width=row_width)

	def news(self, update_button = True):
		buttons = [self.get_close_button()]
		if update_button:
			buttons.append(self.get_update_button("news_update"))
		
		self.keyboard.add(*buttons)
		return self.keyboard


	def add_string_buttons(self, buttons_info: dict):
			buttons = []
			for text, value in buttons_info.items():
				buttons.append(BUTTON(text).inline(value))
			self.keyboard.add(*buttons)

	def settings(self, user_settings_info: tuple):

		get_smile_condition = lambda parameter: '✅' if parameter else '☑'

		timezone = user_settings_info[0]
		receive_notices = user_settings_info[1]
		news_notice = user_settings_info[2]
		delete_old_matches = user_settings_info[3]
		delete_old_events = user_settings_info[4]
		stars_matches_display = user_settings_info[5]
		
		# TIMEZONE
		text_value = get_timezone_text(timezone)
		self.add_string_buttons({'Timezone': "info_button timezone",
								text_value: "settings_change timezone"})

		# NOTIFICATIONS SETTINGS
		self.add_string_buttons({'Notifications': "info_button notifications",
								'▶': "s n"})

		# RECEIVE NOTICES
		text_value = get_smile_condition(receive_notices)
		self.add_string_buttons({'Receive notices': "info_button receive_notices",
								text_value: "settings_change receive_notices"})

		# NOTICE_NEWS
		text_value = get_smile_condition(news_notice)
		self.add_string_buttons({'News notice': "info_button news_notice",
								text_value: "settings_change news_notice"})

		# DELETE MATCHES
		text_value = get_smile_condition(delete_old_matches)
		self.add_string_buttons({'Delete matches': "info_button delete_old_matches",
								text_value: "settings_change delete_old_matches"})

		# DELETE EVENTS
		text_value = get_smile_condition(delete_old_events)
		self.add_string_buttons({'Delete events': "info_button delete_old_events",
								text_value: "settings_change delete_old_events"})

		# 
		#stars_matches_display
		self.add_string_buttons({'Stars display': "info_button stars_matches_display",
								'ALL' if not stars_matches_display else '⭐'*stars_matches_display: "settings_change stars_matches_display"})


		self.keyboard.add(self.get_close_button())

		return self.keyboard

	def notice_start_live(self, match_obj, last_callback_data = 'nsl'):
		match_id = match_obj[0]
		team1_name = match_obj[3]
		team2_name = match_obj[4]
		event_id = match_obj[5]
		event_name = match_obj[6]
		
		url_live = URL().live_broadcast(match_id)
		url_event = URL().event(event_id, event_name)

		self.keyboard.add(BUTTON(f"{team1_name} vs {team2_name}").inline(f"{last_callback_data} mi {match_id}", url=url_live))
		self.keyboard.add(BUTTON(event_name).inline(f"{last_callback_data} ei {event_id}", url=url_event))

		return self.keyboard


	def get_match_button(self, match, last_callback_data, add_time = False, add_live_mark = False, add_url = False, url = None, add = False):
		match_id = match[0]
		match_type = match[1]
		match_time = match[2]
		team1_name = match[3]
		team2_name = match[4]
		#event_id = match[5]
		event_name = match[6]
		result_score = match[7]

		short_time = match_type == 'R'

		if match_type == 'U':
			add_time = True
			button_text = f"{team1_name} vs {team2_name}"

		elif match_type == 'L':
			button_text = f"{'⭕ ' if add_live_mark else ''}{team1_name} vs {team2_name}"

		elif match_type == 'R':
			button_text = f"{team1_name} {result_score[0]} - {result_score[-1]} {team2_name}"

		if add_time and match_type != 'L':
			if short_time:
				match_time = ' '.join(match_time.split()[:2])
			button_text = f"{match_time} | {button_text}" 
		
		match_callback_data = f"{last_callback_data} mi {match_id}"

		# если до этого открывали матчи для ивента и переходили под конкретную игры или открыли матчи из карточки команды
		if 'em mi' in match_callback_data and 'um' in match_callback_data:
			add_url = True
		
		if add_url:
			url = URL().match_or_analytics('M', match_id, team1_name, team2_name, event_name)

		button = BUTTON(button_text).inline(match_callback_data, url=url)
		
		if add:
			self.keyboard.add(button)
			return self.keyboard
		return button


	def matches(self, matches_array: list, last_callback_data: str, date_ = False, add_url = False, url = None, add_live_mark = False):
		if date_:
			match_type = last_callback_data.split()[1]
			button_text = format_date(date_)
			self.keyboard.add(BUTTON(button_text).inline(f"d {match_type}"))

		for match in matches_array:
			self.get_match_button(match, last_callback_data, add_live_mark=add_live_mark, add_url=add_url, add=True)

		if 'ei' in last_callback_data:
			self.keyboard.add(self.get_back_button(last_callback_data, offset=-1))
		else:
			self.keyboard.add(self.get_close_button(), self.get_update_button(last_callback_data))

		return self.keyboard


	def match_info(self, obj: tuple, last_callback_data: str, subscription: bool, team1_url = None, team2_url = None, event_url = None):
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

		# URLS
		url_match = URL().match_or_analytics('M', match_id, team1_name, team2_name, event_name)
		url_analytics = URL().match_or_analytics('A',match_id, team1_name, team2_name, event_name)
		
		# TEXT
		stars_meta_text =f"{'⭐'*stars} {'bo' if meta.isdigit() else ''}{meta}"

		# CALLBACK_DATA		
		team1_info = f"{last_callback_data} ti {team1_id}"
		team2_info = f"{last_callback_data} ti {team2_id}"

		callback_data = ' '.join(last_callback_data.split()[:-2])
		
		if 'ei' not in last_callback_data:
			callback_data = f"{last_callback_data} ei {event_id}"

		# если до этого открывали матчи для ивента или матчи/результаты для команды
		if 'em' in last_callback_data_split or 'um' in last_callback_data_split or 'rm' in last_callback_data_split:
			team1_url = URL().team(team1_id, team1_name)
			team2_url = URL().team(team2_id, team2_name)

		# если до этого открывали матчи/результаты для команды
		if 'um' in last_callback_data_split or 'rm' in last_callback_data_split:
			event_url = URL().event(event_id, event_name)

		# BUTTONS
		button_team1_name = BUTTON(team1_name).inline(team1_info, url=team1_url)
		button_team2_name = BUTTON(team2_name).inline(team2_info, url=team2_url)
		button_time = BUTTON(date_time_char).inline(f"look_info {date_time_char}")
		button_stars_meta = BUTTON(stars_meta_text).inline(f"look_info {stars_meta_text}")
		button_event_name = BUTTON(event_name).inline(callback_data, url=event_url)
		button_match_info = BUTTON('Match info').inline('match_info_url', url=url_match)
		button_analytics = BUTTON('Analytics').inline('analytics_url', url=url_analytics)
		button_back = self.get_back_button(last_callback_data)
		button_subscribe = self.get_subscribe_button(subscription, last_callback_data)
		
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
			
			button_result_score = BUTTON(result_text).inline(f"look_info {result_text}")
			buttons_first_string.insert(1, button_result_score)

		self.keyboard.add(*buttons_first_string)
		self.keyboard.add(*buttons_second_string)
		self.keyboard.add(button_event_name)
		self.keyboard.add(button_match_info, button_analytics)
		self.keyboard.add(button_back, button_subscribe)

		return self.keyboard


	def matches_by_team_id(self, matches_array: tuple, last_callback_data, add_live_mark = True):

		for match in matches_array:

			self.get_match_button(match, last_callback_data, add_time=True, add_live_mark=add_live_mark, add_url=False, add=True)

		self.keyboard.add(self.get_back_button(last_callback_data))
		
		return self.keyboard


	def notifications(self, d: tuple, last_callback_data, add_back_button = False, add_close_button = True, add_team_flag = True):
		
		texts = {'teams': '🌀 Teams 🌀', 
				'matches': '🆚 Matches 🆚', 
				'events': '🎯 Events 🎯'
			}

		for notice_type, obj in d.items():
			
			text_button_notice_type = texts[notice_type]
			self.keyboard.add(BUTTON(text_button_notice_type).inline(f"notice_info {notice_type}"))

			for x in obj:

				if notice_type == 'teams':
					self.keyboard.add(self.get_team_button(x, last_callback_data, add_flag=add_team_flag))

				elif notice_type == 'matches':
					self.get_match_button(x, last_callback_data, add_time=True, add_live_mark=True, add=True)

				elif notice_type == 'events':
					self.keyboard.add(self.get_event_button(x, last_callback_data))

		if not last_callback_data is None and 's' in last_callback_data.split():
			add_back_button = True
			add_close_button = False

		last_row_buttons = []
		
		if add_back_button:
			last_row_buttons.append(self.get_back_button(last_callback_data, offset=-1))

		if add_close_button:
			last_row_buttons.append(self.get_close_button())

		self.keyboard.add(*last_row_buttons)

		return self.keyboard


	def get_team_button(self, obj, last_callback_data: str, add_flag = False):
		team_id = obj[0]
		team_name = obj[1]
		flag = obj[2]

		text_button = f"{team_name} {'' if not add_flag or flag is None else flag}"
		callback_data = f"{last_callback_data} ti {team_id}"
		
		return BUTTON(text_button).inline(callback_data)

	def get_player_button(self, obj, last_callback_data: str):
		player_id = obj[0]
		player_nik_name = obj[1]
		player_name = obj[2]
		flag = obj[3]

		text_button = player_nik_name
		callback_data = f"{last_callback_data} pi {player_id}"
		
		return BUTTON(text_button).inline(callback_data)

	def teams_list(self, all_teams_obj: tuple, last_callback_data: str, add_flag = False):

		for team_obj in all_teams_obj:
			self.keyboard.add(self.get_team_button(team_obj, last_callback_data, add_flag=add_flag))

		self.keyboard.add(self.get_close_button())

		return self.keyboard


	def players_list(self, all_players_obj: tuple, last_callback_data: str):

		for player_obj in all_players_obj:
			self.keyboard.add(self.get_player_button(player_obj, last_callback_data))

		self.keyboard.add(self.get_close_button())

		return self.keyboard

	
	def team_info(self, obj: tuple, last_callback_data: str, subscription: bool):
		team_id = obj[0]
		team_name = obj[1]
		flag = obj[2]

		# TEXT AND URL
		url_team = URL().team(team_id, team_name)

		# BUTTONS
		button_team_name = BUTTON(f"{team_name} {'' if flag is None else flag}").inline(team_id, url=url_team)
		button_details = BUTTON("Details").inline(f"{last_callback_data} dt {team_id}")
		button_upcoming_matches = BUTTON("Upcoming matches").inline(f"{last_callback_data} um {team_id}")
		button_results_matches = BUTTON("Results of matches").inline(f"{last_callback_data} rm {team_id}")
		button_events = BUTTON("Events").inline(f"{last_callback_data} etm {team_id}")
		button_back = self.get_back_button(last_callback_data)
		button_subscribe = self.get_subscribe_button(subscription, last_callback_data)
		
		# ADD BUTTONS
		self.keyboard.add(button_team_name)
		self.keyboard.add(button_details)
		self.keyboard.add(button_upcoming_matches)
		self.keyboard.add(button_results_matches)
		self.keyboard.add(button_events)
		self.keyboard.add(button_back, button_subscribe)

		return self.keyboard

	def player_info(self, obj: tuple, last_callback_data: str):
		player_id = obj[0]
		player_nik_name = obj[1]
		player_name = obj[2]
		flag = obj[3]
		number_maps = obj[4]
		number_rounds = obj[5]
		kd_diff = obj[6]
		kd = obj[7]
		rating = obj[8]

		# TEXT AND URL
		url_player = URL().player(player_id, player_nik_name)

		# BUTTONS
		button_player_nik_name = BUTTON(f"{player_nik_name} {'' if flag is None else flag}").inline(player_id, url=url_player)
		button_player_name = BUTTON(player_name).inline(player_id, url=url_player)
		button_back = self.get_back_button(last_callback_data)

		# ADD BUTTONS
		self.keyboard.add(button_player_nik_name, button_player_name)
		#self.keyboard.add(button_player_name)

		self.add_string_buttons({'Maps': "info_button number_maps",
								number_maps: f"look_info {number_maps}"})

		self.add_string_buttons({'Rounds': "info_button number_rounds",
								number_rounds: f"look_info {number_rounds}"})

		kd_diff_text = f"{kd_diff} {'🔻' if kd_diff < 0 else '🆙'}"
		self.add_string_buttons({'K-D Diff': "info_button kd_diff",
								kd_diff_text : f"look_info {kd_diff_text}"})

		self.add_string_buttons({'K/D': "info_button kd",
								kd: f"look_info {kd}"})

		self.add_string_buttons({'Rating 1.0': "info_button rating",
								rating: f"look_info {rating}"})

		self.keyboard.add(button_back)

		return self.keyboard


	def details_by_team(self, details: tuple, last_callback_data: str):
		team_id = details[0]
		team_name = details[1]
		flag = details[2]
		number_maps = details[3]
		kd_diff = details[4]
		kd = details[5]
		rating = details[6]

		# TEXT
		url_team = URL().team(team_id, team_name)

		# BUTTONS
		button_team_name = BUTTON(f"{team_name} {'' if flag is None else flag}").inline(team_id, url=url_team)
		button_back = self.get_back_button(last_callback_data)

		# ADD BUTTONS
		self.keyboard.add(button_team_name)

		self.add_string_buttons({'Maps': "info_button number_maps",
								number_maps: f"look_info {number_maps}"})

		kd_diff_text = f"{kd_diff} {'🔻' if kd_diff < 0 else '🆙'}"
		self.add_string_buttons({'K-D Diff': "info_button kd_diff",
								kd_diff_text : f"look_info {kd_diff_text}"})

		self.add_string_buttons({'K/D': "info_button kd",
								kd: f"look_info {kd}"})

		self.add_string_buttons({'Rating 1.0': "info_button rating",
								rating: f"look_info {rating}"})

		self.keyboard.add(button_back)
		
		return self.keyboard


	def timezones(self):
		# config
		timezones_array_minus = ('12:00','11:00','10:00','9:30','9:00','8:00','7:00','6:00','5:00','4:00','3:30','3:00','2:00','1:00')
		timezones_array_plus = ('0:00','1:00','2:00','3:00','3:30','4:00','4:30','5:00','5:30','5:45','6:00','6:30','7:00','8:00','8:45','9:00','10','10:30','11:00','12:00','12:45','13:00','14:00')

		buttons_minus = [BUTTON(f"UTC−{x}").inline(datetime.timedelta(hours=-int(x.split(':')[0]), minutes=-int(x.split(':')[-1]))) for x in timezones_array_minus]
		buttons_plus = [BUTTON(f"UTC+{x}").inline(datetime.timedelta(hours=int(x.split(':')[0]), minutes=int(x.split(':')[-1]))) for x in timezones_array_plus]

		self.keyboard.add(*buttons_minus, *buttons_plus)

		return self.keyboard

	
	def dates(self, match_type: str, dates_array: list):
		for date_ in dates_array:
			button_text = format_date(date_[0])
			self.keyboard.add(BUTTON(button_text).inline(f"d {match_type} m {date_[0]}"))

		self.keyboard.add(self.get_close_button())

		return self.keyboard


	def events_type(self):
		events_type_dict = {'O': "Ongoing events", 'B': "Big events", 'S': "Small events"}
		self.keyboard.add(*[BUTTON(text).inline(f"et ebt {events_type}") for events_type, text in events_type_dict.items()])
		self.keyboard.add(self.get_close_button())
		return self.keyboard


	def events(self, event_type: str, events_array: list, last_callback_data: str, add_months = True, add_url = False, add_back_button = True, add_close_button = False, url = None):
		last_month = ''
		for event in events_array:
			event_id = event[0]
			event_name = event[1]
			start_date = event[2]
			
			month = start_date.strftime("%B")
			if add_months and event_type != 'O' and month != last_month:
				smile = SEASSONS_SMILE(month)
				month_text = f"{smile} {month} {smile}"
				self.keyboard.add(BUTTON(month_text).inline(f"look_info {month_text}"))
				last_month = month
			
			if add_url:
				url = URL().event(event_id, event_name)

			button_event = BUTTON(event_name).inline(f"{last_callback_data} ei {event_id}", url=url)
			self.keyboard.add(button_event)

		if add_back_button:
			self.keyboard.add(self.get_back_button(last_callback_data))
		else:
			self.keyboard.add(self.get_close_button())
		
		return self.keyboard

	
	def events_by_team(self, events_array: list, last_callback_data: str):
		return self.events(None, events_array, last_callback_data, add_months=False, add_url=True)

	
	def events_by_date(self, events_array: list, last_callback_data: str):
		return self.events(None, events_array, last_callback_data, add_back_button=False)

	
	def event_info(self, obj: tuple, last_callback_data: str, subscription: bool):
		def get_date_text(date_):
			date_convert = datetime.datetime.strftime(date_, '%b %#d')
			days = str(date_.day)
			try:
				if days[0] == '1': raise Exception
				ending = {'1':'st', '2':'nd', '3':'rd'}[days[-1]]
			except:
				ending = 'th'
			return f"{date_convert}{ending}"

		event_id = obj[0]
		#event_type = obj[1]
		event_name = obj[2]
		event_location = obj[3]
		flag = obj[4]
		start_date = get_date_text(obj[5])
		stop_date = get_date_text(obj[6])
		prize = obj[7]
		count_teams = obj[8]

		# TEXT
		url_event = URL().event(event_id, event_name)
		location_text = f"{flag} {event_location}"
		dates_text = f"{start_date} — {stop_date}"
		prize_text = f"Prize: {'' if prize is None else '💲'}{prize if prize is None else '{:,}'.format(prize)}"
		teams_text = f"Teams: {count_teams}"

		# CALLBACK DATA 
		callback_data = f"{last_callback_data} em"

		# ADD BUTTONS
		button_event_name = BUTTON(event_name).inline("event_name", url=url_event)
		button_location = BUTTON(location_text).inline(f"look_info {location_text}")
		button_date = BUTTON(dates_text).inline(f"look_info {dates_text}")
		button_prize = BUTTON(prize_text).inline(f"look_info {prize_text}")
		button_teams = BUTTON(teams_text).inline(f"look_info {teams_text}")
		button_matches = BUTTON("All Matches").inline(callback_data)
		button_back = self.get_back_button(last_callback_data)
		button_subscribe = self.get_subscribe_button(subscription, last_callback_data)

		self.keyboard.add(button_event_name)
		self.keyboard.add(button_location, button_date)
		self.keyboard.add(button_prize, button_teams)
		self.keyboard.add(button_matches)
		self.keyboard.add(button_back, button_subscribe)

		return self.keyboard


	def get_event_button(self, obj, last_callback_data):
		event_id = obj[0]
		event_name = obj[1]
	
		text_button = event_name
		callback_data = f"{last_callback_data} ei {event_id}"

		return BUTTON(text_button).inline(callback_data)


	def get_close_button(self):
		return BUTTON("❌").inline("close")

	def get_update_button(self, callback_data):
		return BUTTON("🔄").inline(callback_data)

	def get_back_button(self, last_callback_data, offset=-2):
		if offset is None:
			back_callback_data = last_callback_data
		else:
			back_callback_data = ' '.join(last_callback_data.split()[:offset])
		return BUTTON("⬅◀").inline(back_callback_data)

	def get_subscribe_button(self, subscription, last_callback_data):
		subscription_to_notifications = f"notice {last_callback_data}"
		return BUTTON('✅' if subscription else '➕').inline(subscription_to_notifications)