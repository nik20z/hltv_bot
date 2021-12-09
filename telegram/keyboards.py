import datetime
import re

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.types import KeyboardButton, InlineKeyboardButton

from functions import get_timezone_text
from data.config import MAIN_URL




format_date = lambda date_: datetime.datetime.strftime(date_, '%#d %b (%A)')



class URL:
	
    def join_hyphen(self, text: str):
        if text != None:
            return '-'.join(text.lower().split())

    def event(self, event_id: int, event_name: str):
        return f"{MAIN_URL}events/{event_id}/{self.join_hyphen(event_name)}"

    def match_or_analytics(self, type_: str, scorebot_id: int, team1_name: str, team2_name: str, event_name: str):
        try:
            type_text = {'M': 'matches/', 'A': 'betting/analytics/'}[type_]
            return f"{MAIN_URL}{type_text}{scorebot_id}/{self.join_hyphen(team1_name)}-vs-{self.join_hyphen(team2_name)}-{self.join_hyphen(event_name)}"
        except:
            return MAIN_URL
    
    def team(self, team_id: int, team_name: str):
        return f"{MAIN_URL}team/{team_id}/{self.join_hyphen(team_name)}"

    def player(self):
        pass



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

	def news(self):
		self.keyboard.add(BUTTON("❌").inline('close'), BUTTON("🔄").inline("news_update"))
		return self.keyboard

	def settings(self, user_info: tuple):
		def get_text_value(text, callback_data, value):
			get_smile_condition = lambda parameter: '✅' if parameter else '☑'
			
			if callback_data == 'timezone':
				text = get_timezone_text(value)
			elif callback_data in ['live_notification']:
				text = get_smile_condition(value)
			return text

		timezone = user_info[0]
		live_notification = user_info[1]

		settings_dict = {'Timezone': timezone, 
						'Live notification': live_notification} 

		for text, value in settings_dict.items():
			callback_data = '_'.join(text.lower().split())
			text_value = get_text_value(text, callback_data, value)

			button_info = BUTTON(text).inline(f"settings info {callback_data}")
			button_value = BUTTON(text_value).inline(f"settings {callback_data}")

			self.keyboard.add(button_info, button_value)


		return self.keyboard

	def matches(self, matches_array: list, last_callback_data: str, date_ = False, live_mark = False):
		if date_:
			match_type = last_callback_data.split()[1]
			button_text = format_date(date_)
			self.keyboard.add(BUTTON(button_text).inline(f"d {match_type}"))

		for match in matches_array:
			scorebot_id = match[0]
			match_type = match[1]
			match_time = match[2]
			team1_name = match[3]
			team2_name = match[4]
			#event_id = match[5]
			results_score = match[6]

			if match_type == 'U':
				button_text = f"{match_time} | {team1_name} vs {team2_name}"

			elif match_type == 'L':
				button_text = f"{'⭕ ' if live_mark else ''}{team1_name} vs {team2_name}"

			elif match_type == 'R':
				button_text = f"{team1_name} {results_score[0]} - {results_score[-1]} {team2_name}"
			
			match_callback_data = f"{last_callback_data} mi {scorebot_id}"

			self.keyboard.add(BUTTON(button_text).inline(match_callback_data))		

		if 'ei' in last_callback_data:
			back_callback_data = ' '.join(last_callback_data.split()[:-2])
			self.keyboard.add(BUTTON("⬅◀").inline(back_callback_data))
		else:
			self.keyboard.add(BUTTON("❌").inline('close'), BUTTON("🔄").inline(last_callback_data))

		return self.keyboard


	def match_info(self, obj: tuple, last_callback_data: str):
		scorebot_id = obj[0]
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

		# URLS
		url_match = URL().match_or_analytics('M', scorebot_id, team1_name, team2_name, event_name)
		url_analytics = URL().match_or_analytics('A',scorebot_id, team1_name, team2_name, event_name)
		url_team1 = URL().team(team1_id, team1_name)
		url_team2 = URL().team(team2_id, team2_name)
		
		# TEXT
		stars_meta_text =f"{'⭐'*stars} {'bo' if meta.isdigit() else ''}{meta}"

		# CALLBACK_DATA
		back_callback_data = ' '.join(last_callback_data.split()[:-2])
		callback_data = back_callback_data
		
		if 'ei' not in last_callback_data:
			callback_data = f"{last_callback_data} ei {event_id}"

		# BUTTONS
		button_team1_name = BUTTON(team1_name).inline(team1_id, url=url_team1)
		button_team2_name = BUTTON(team2_name).inline(team2_id, url=url_team2)
		button_time = BUTTON(date_time_char).inline('time')
		button_stars_meta = BUTTON(stars_meta_text).inline('stars')
		button_event_name = BUTTON(event_name).inline(callback_data)
		button_match_info = BUTTON('Match info').inline('match_info_url', url=url_match)
		button_analytics = BUTTON('Analytics').inline('analytics_url', url=url_analytics)
		button_back = BUTTON("⬅◀").inline(back_callback_data)
		
		# ADD BUTTONS
		if match_type == 'R':
			button_result_score = BUTTON(f"{result_score[0]} - {result_score[-1]}").inline("result_score")
			self.keyboard.add(button_team1_name, button_result_score, button_team2_name)
		else:
			self.keyboard.add(button_team1_name, button_team2_name)
		
		self.keyboard.add(button_time, button_stars_meta)
		self.keyboard.add(button_event_name)
		self.keyboard.add(button_match_info, button_analytics)
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
		return self.keyboard


	def events_type(self):
		events_type_dict = {'O': "Ongoing events", 'B': "Big events", 'S': "Small events"}
		self.keyboard.add(*[BUTTON(text).inline(f"events_by_type {events_type}") for events_type, text in events_type_dict.items()])
		self.keyboard.add(BUTTON("❌").inline("close"))
		return self.keyboard

	def events_by_type(self, events_array: list, last_callback_data: str):
		for event in events_array:
			event_id = event[0]
			event_name = event[1]
			self.keyboard.add(BUTTON(event_name).inline(f"{last_callback_data} ei {event_id}"))
		self.keyboard.add(BUTTON("⬅").inline(f"{last_callback_data} events_type {event_id}"))
		return self.keyboard


	def event_info(self, obj: tuple, last_callback_data: str):
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
		#teams_id = obj[9]

		url_event = URL().event(event_id, event_name)
		location_text = f"{flag} {event_location}"
		prize_text = f"Prize: {'' if prize is None else '💲'}{prize if prize is None else '{:,}'.format(prize)}"
		teams_text = f"Teams: {count_teams}"

		button_event_name = BUTTON(event_name).inline("event_name", url=url_event)
		button_location = BUTTON(location_text).inline("location")
		button_date = BUTTON(f"{start_date} — {stop_date}").inline("date")
		button_prize = BUTTON(prize_text).inline("prize")
		button_teams = BUTTON(teams_text).inline("event_teams")

		callback_data = f"{last_callback_data} em {event_id}"
		button_matches = BUTTON("All Matches").inline(callback_data)

		back_callback_data = ' '.join(last_callback_data.split()[:-2])
		button_back = BUTTON("⬅◀").inline(back_callback_data)

		self.keyboard.add(button_event_name)
		self.keyboard.add(button_location, button_date)
		self.keyboard.add(button_prize, button_teams)
		self.keyboard.add(button_matches)
		self.keyboard.add(button_back)

		return self.keyboard
	


