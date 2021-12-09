import time

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import LoggingConnection, LoggingCursor

from functions import time_of_function



# SELECT ---------------------------------------------------------------------------------------------------

# ---> [TABLE telegram]

# Получаем всю информацию о пользователе
query_select_user_info = lambda user_id: "SELECT * FROM telegram WHERE id = {0}".format(user_id)

# Получаем timezone пользователя по его id
query_select_user_timezone = lambda user_id: "SELECT timezone FROM telegram WHERE id = {0}".format(user_id)

# Получаем настройки пользователя (timezone, live_notification) по его id 
query_select_user_settings = lambda user_id: "SELECT timezone, live_notification FROM telegram WHERE id = {0}".format(user_id)

# Получаем массив id закбокированнных пользователей
query_select_blocked_users = "SELECT id FROM telegram WHERE ban"

# ---> [TABLE matches]

# Получаем матчи с учётом их типа (match_type), даты (date_) и часового пояса (timezone) пользователя 
query_select_matches = lambda match_type, date_, timezone: """SELECT matches.id, matches.type, to_char(unix_datetime::time + interval '{2}', 'HH24:MI'), tm1.name, tm2.name, events.id, result_score 
																FROM matches 
																LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
																LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
																LEFT JOIN events ON (matches.event_id = events.id) 
																WHERE matches.type = '{0}' 
																	AND (unix_datetime + interval '{2}')::date = date '{1}' 
																	AND tm2.name NOTNULL
																ORDER BY unix_datetime;
																""".format(match_type, date_, timezone)

# Получаем матчи с учётом их принадлежности к конкретному событию (event_id) И сразу же вносим правку на часовой пояс пользоватя (timezone)
query_select_matches_by_event_id = lambda event_id, timezone: """SELECT matches.id, matches.type, to_char(unix_datetime + interval '{1}', 'DD Mon HH24:MI'), tm1.name, tm2.name, event_id, result_score 
																	FROM matches
																	LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
																	LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id)
																	WHERE event_id = {0} 
																		AND tm2.name NOTNULL
																	ORDER BY unix_datetime;
																	""".format(event_id, timezone)

# Получаем данные о прямых трансляциях
query_select_live_matches = """SELECT matches.id, matches.type, unix_datetime, tm1.name, tm2.name, events.id, result_score 
								FROM matches
								LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
								LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
								LEFT JOIN events ON (matches.event_id = events.id) 
								WHERE matches.type = 'L'
								"""

# Получаем информацию о матче по его id (scorebot_id) и сразу же вносим правку на часовой пояс (timezone) пользователя 
query_select_match_info = lambda scorebot_id, timezone: """SELECT matches.id, matches.type, to_char(unix_datetime + interval '{1}', 'HH24:MI (DD Mon)'), stars, meta, tm1.id, tm1.name, tm2.id, tm2.name, events.id, events.name, result_score 
															FROM matches
															LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
															LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id)
															LEFT JOIN events ON (matches.event_id = events.id) 
															WHERE matches.id = {0};
															""".format(scorebot_id, timezone)

#!!!!!!!!!!!!!!!! current_date привязывается к часовому поясу сервера!!!
# Получаем массив дат с учётом часового пояса (user_timezone), напрвления отбора (comparison_sign - больше-равно или меньше-равно), количества дней (count_days) и сдвига (offset_days)
query_select_dates = lambda user_timezone, comparison_sign, sort_type, count_days: """SELECT distinct (unix_datetime + interval '{0}')::date AS date_
																							FROM matches
																							WHERE (unix_datetime + interval '{0}')::date {1} current_date
																							ORDER BY date_ {2}
																							LIMIT {3};
																							""".format(user_timezone, comparison_sign, sort_type, count_days)


# ---> [TABLE teams]

# Получаем id команды по её названию 
query_select_team_id_by_name = lambda team_name: "SELECT id FROM teams WHERE name = '{0}'".format(team_name)


# ---> [TABLE events]

# Получаем данные об ивентах по их типу (event_type) и сдвигаем выборку на определённое количество дней назад 
query_select_events_by_type = lambda event_type, offset_days: """SELECT id, name, stop_date 
																	FROM events
																	WHERE type = '{0}' 
																		AND events.stop_date > current_date - interval '{1} days'
																	ORDER BY events.start_date;
																	""".format(event_type, offset_days)

# Получаем данные о текущих событиях (на основе start_date и stop_date)
query_select_events_by_type_ongoing = """SELECT id, name, start_date, stop_date 
											FROM events
											WHERE events.start_date <= current_date 
												AND events.stop_date >= current_date
											ORDER BY events.start_date;
											"""

# Получаем информацию о событии по его id (event_id)
query_select_event_info = lambda event_id: """SELECT id, type, name, location, flag, start_date, stop_date, prize, count_teams, teams_id 
												FROM events
												WHERE id = {0}""".format(event_id)

# Получаем id события по его названию
query_select_event_id_by_name = lambda event_name: "SELECT id FROM events WHERE name = '{0}'".format(event_name)


# ---> [TABLE news]

# Получаем данные о новостях
query_select_news = lambda number_of_articles: """SELECT id, news_text, flag, href 
													FROM news 
													ORDER BY id DESC 
													LIMIT {0};""".format(number_of_articles)



# INSERT ---------------------------------------------------------------------------------------------------------------

# ---> [TABLE telegram]

# Инсертим данные о новом пользователе
query_insert_new_user = "INSERT INTO telegram (id, name, joined) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING"


# ---> [TABLE matches]

# Инсертим данные о матчах
query_insert_matches = """INSERT INTO matches
							(id, type, unix_datetime, stars, lan, team1_id, team2_id, meta, event_id, result_score)
							VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
							ON CONFLICT (id) DO UPDATE
							SET (type, unix_datetime, team1_id, team2_id, meta, event_id, result_score)
							= (EXCLUDED.type, EXCLUDED.unix_datetime, EXCLUDED.team1_id, EXCLUDED.team2_id, EXCLUDED.meta, EXCLUDED.event_id, EXCLUDED.result_score)
							"""

# ---> [TABLE teams]

# Инсертим данные о командах
query_insert_teams = "INSERT INTO teams (id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING"


# ---> [TABLE events]

# Инсертим данные о событиях
query_insert_events = """INSERT INTO events
						(id, type, name, location, flag, start_date, stop_date, prize, teams_id, count_teams)
						VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
						ON CONFLICT (id) DO UPDATE
						SET (location, flag, start_date, stop_date, prize, teams_id, count_teams)
						= (EXCLUDED.location, EXCLUDED.flag, EXCLUDED.start_date, EXCLUDED.stop_date, EXCLUDED.prize, EXCLUDED.teams_id, EXCLUDED.count_teams)
						"""


# ---> [TABLE news]

# Инсертим данные о новостях
query_insert_news = "INSERT INTO news (id, news_text, flag, href) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING"



# UPDATE -----------------------------------------------------------------------------------------------------------

# ---> [TABLE telegram]

# Обновляем часовой пояс пользователя (timezone) по егo id (user_id)
query_update_user_timezone = lambda user_id, timezone: "UPDATE telegram SET timezone = '{1}' WHERE id = {0}".format(user_id, timezone)

# Обновляем данные о булевых значениях настроек по id пользователя (user_id) и названию параметра (colomn_name)
query_update_user_bool_parameter = lambda user_id, colomn_name:  "UPDATE telegram SET {1} = NOT telegram.{1} WHERE id = {0}".format(user_id, colomn_name)




class SELECT:

	def user_info(self, user_id = None):
		if user_id is None:
			cursor.execute("SELECT id FROM telegram")
			return [x[0] for x in cursor.fetchall()]
		cursor.execute(query_select_user_info(user_id))
		return cursor.fetchone()

	def user_settings(self, user_id: int):
		cursor.execute(query_select_user_settings(user_id))
		return cursor.fetchone()

	def user_timezone(self, user_id: int):
		cursor.execute(query_select_user_timezone(user_id))
		return cursor.fetchone()[-1]

	def event_id_by_name(self, event_name: str):
		cursor.execute(query_select_event_id_by_name(event_name))
		return cursor.fetchone()

	# УЗНАТЬ, КАК МОЖНО ОПТИМИЗИРОВАТЬ ЭТОТ ЗАПРОС
	def team_id_by_name(self, team_name: str):
		cursor.execute(query_select_team_id_by_name(team_name))
		return cursor.fetchone()

	def matches(self, match_type: str, date_, timezone):
		cursor.execute(query_select_matches(match_type, date_, timezone))
		if match_type == 'R':
			return cursor.fetchall()[::-1]
		return cursor.fetchall()

	def matches_by_event_id(self, event_id: int, timezone):
		cursor.execute(query_select_matches_by_event_id(event_id, timezone))
		return cursor.fetchall()

	def match_info(self, scorebot_id: int, timezone):
		cursor.execute(query_select_match_info(scorebot_id, timezone))
		return cursor.fetchone()

	def live_matches(self):
		cursor.execute(query_select_live_matches)
		return cursor.fetchall()

	def dates(self, user_timezone, match_type: str, comparison_sign = '>=', sort_type = '', count_days = 7):
		if match_type == 'R':
			comparison_sign = '<='
			sort_type = 'DESC'
		cursor.execute(query_select_dates(user_timezone, comparison_sign, sort_type, count_days))
		return cursor.fetchall()

	def events_by_type(self, event_type: str, offset_days = 3):
		cursor.execute(query_select_events_by_type(event_type, offset_days))
		return cursor.fetchall()

	def events_by_type_ongoing(self):
		cursor.execute(query_select_events_by_type_ongoing)
		return cursor.fetchall()

	def event_info(self, event_id: int):
		cursor.execute(query_select_event_info(event_id))
		return cursor.fetchone()

	def news(self, number_of_articles = 15):
		cursor.execute(query_select_news(number_of_articles))
		return cursor.fetchall()

	def blocked_user_ids(self):
		cursor.execute(query_select_blocked_users)
		return [x[0] for x in cursor.fetchall()]



class INSERT:

	def new_user(self, new_user_data: tuple):
		cursor.execute(query_insert_new_user, new_user_data)

	def matches(self, matches_data: tuple):
		cursor.executemany(query_insert_matches, matches_data)
		connection.commit()

	def teams(self, teams_data: tuple):
		cursor.executemany(query_insert_teams, teams_data)
		connection.commit()

	def events(self, events_data: tuple):
		cursor.executemany(query_insert_events, events_data)
		connection.commit()

	def news(self, news_data: tuple):
		cursor.executemany(query_insert_news, news_data)
		connection.commit()



class UPDATE:
	
	def user_timezone(self, user_id: int, timezone):
		cursor.execute(query_update_user_timezone(user_id, timezone))
		connection.commit()

	def user_bool_parameter(self, user_id: int, colomn_name: str):
		cursor.execute(query_update_user_bool_parameter(user_id, colomn_name))
		connection.commit()



class DELETE:
	def function():
		pass



class TABLE:
	def function():
		pass








def CONNECT(db_settings: dict):
	global connection
	global cursor

	connection = psycopg2.connect(**db_settings)
	connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
	cursor = connection.cursor()

	cursor.execute("SELECT version();")
	record = cursor.fetchone()
	print("Вы подключены к - ", record, "\n")


	return TABLE(), INSERT(), UPDATE(), SELECT(), DELETE()


'''
ускоряет выполнение запроса при больших объёмах

#args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", x) for x in matches_object)
#cur.execute("INSERT INTO matches VALUES " + args_str)
#connection.commit()

'''