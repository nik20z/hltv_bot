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
query_select_user_settings = lambda user_id: "SELECT timezone, receive_notices, news_notice, delete_old_matches, delete_old_events, stars_matches_display FROM telegram WHERE id = {0}".format(user_id)

# Получаем массив id закбокированнных пользователей
query_select_blocked_users = "SELECT id FROM telegram WHERE ban"

# 
query_select_user_ids_for_notice = lambda match_id, team1_id, team2_id, event_id: """WITH updated AS (UPDATE telegram SET notice_matches = CASE
																								WHEN id = telegram.id AND telegram.delete_old_matches 
																									THEN array_remove(notice_matches, {0})
																								ELSE notice_matches
																								END)
																						SELECT id FROM telegram 
																						WHERE telegram.receive_notices AND 
																							({0} = ANY (notice_matches) OR 
																							{1} = ANY (notice_teams) OR
																							{2} = ANY (notice_teams) OR
																							{3} = ANY (notice_events));
																						""".format(match_id, team1_id, team2_id, event_id)

# 
'''
query_select_notice = lambda user_id, id_, colomn_name: """SELECT CASE 
																WHEN id = {0} AND {1} = ANY ({2})
																THEN 1
																ELSE 0
																END
															FROM telegram
															""".format(user_id, id_, colomn_name)
'''

query_select_notice = lambda user_id, id_, colomn_name: """SELECT 1 FROM telegram
																WHERE id = {0} AND {1} = ANY ({2});
															""".format(user_id, id_, colomn_name)

# 
query_select_all_notice = lambda user_id: "SELECT 'teams', notice_teams, 'matches', notice_matches, 'events', notice_events FROM telegram WHERE id = {0}".format(user_id)

# 
query_select_user_ids_for_news_notice = "SELECT id FROM telegram WHERE news_notice"


# ---> [TABLE matches]

# Получаем матчи с учётом их типа (match_type), даты (date_) и часового пояса (timezone) пользователя 
query_select_matches = lambda match_type, date_, timezone, stars_matches_display, type_sort: """SELECT matches.id, matches.type, to_char(unix_datetime::time + interval '{2}', 'HH24:MI'), tm1.name, tm2.name, event_id, ev.name, result_score 
																FROM matches 
																LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
																LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
																LEFT JOIN events as ev ON (matches.event_id = ev.id) 
																WHERE matches.type = '{0}' 
																	AND (unix_datetime + interval '{2}')::date = date '{1}' 
																	AND matches.stars >= {3} 
																	AND tm2.name NOTNULL
																ORDER BY unix_datetime {4};
																""".format(match_type, date_, timezone, stars_matches_display, type_sort)

# Получаем матчи с учётом их принадлежности к конкретному событию (event_id) И сразу же вносим правку на часовой пояс пользоватя (timezone)
query_select_matches_by_event_id = lambda event_id, timezone: """SELECT matches.id, matches.type, to_char(unix_datetime + interval '{1}', 'DD Mon HH24:MI'), tm1.name, tm2.name, event_id, ev.name, result_score 
																	FROM matches
																	LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
																	LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id)
																	LEFT JOIN events as ev ON (matches.event_id = ev.id) 
																	WHERE event_id = {0} 
																		AND tm2.name NOTNULL
																	ORDER BY unix_datetime;
																	""".format(event_id, timezone)

# Получаем данные о прямых трансляциях
query_select_live_matches = """SELECT matches.id, matches.type, unix_datetime, tm1.name, tm2.name, event_id, ev.name, result_score 
								FROM matches
								LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
								LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
								LEFT JOIN events as ev ON (matches.event_id = ev.id) 
								WHERE matches.type = 'L'
								"""

# 
query_select_live_matches_for_notice = """SELECT matches.id, stars, team1_id, tm1.name, team2_id, tm2.name, event_id, ev.name, result_score FROM matches 
											LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
											LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
											LEFT JOIN events as ev ON (matches.event_id = ev.id) 
											WHERE matches.type = 'L'"""

# Получаем информацию о матче по его id (scorebot_id) и сразу же вносим правку на часовой пояс (timezone) пользователя 
query_select_match_info = lambda scorebot_id, timezone: """SELECT matches.id, matches.type, to_char(unix_datetime + interval '{1}', 'HH24:MI (DD Mon)'), stars, meta, tm1.id, tm1.name, tm2.id, tm2.name, event_id, ev.name, result_score 
															FROM matches
															LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
															LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id)
															LEFT JOIN events as ev ON (matches.event_id = ev.id) 
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

# 
query_select_matches_by_ids_array = lambda ids_array, timezone:"""SELECT m.id, m.type, to_char(unix_datetime + interval '{1}', 'DD Mon HH24:MI'), tm1.name, tm2.name, event_id, ev.name, result_score
																	FROM unnest(ARRAY[{0}]) match_id
																	LEFT JOIN matches m on m.id = match_id
																	LEFT JOIN teams as tm1 ON (m.team1_id = tm1.id) 
																	LEFT JOIN teams as tm2 ON (m.team2_id = tm2.id)
																	LEFT JOIN events as ev ON (m.event_id = ev.id) 
																	ORDER BY unix_datetime DESC
																	""".format(ids_array, timezone)

# 
query_select_matches_by_team_id = lambda team_id, match_type, timezone, sort_type, offset: """SELECT matches.id, matches.type, to_char(unix_datetime + interval '{2}', 'DD Mon HH24:MI'), tm1.name, tm2.name, event_id, ev.name, result_score 
																					FROM matches 
																					LEFT JOIN teams as tm1 ON (matches.team1_id = tm1.id) 
																					LEFT JOIN teams as tm2 ON (matches.team2_id = tm2.id) 
																					LEFT JOIN events as ev ON (matches.event_id = ev.id) 
																					WHERE (matches.type = '{1}' OR matches.type = 'L')
																					AND (tm1.id = {0} OR tm2.id = {0})
																					AND tm2.name NOTNULL
																					ORDER BY unix_datetime {3}
																					LIMIT {4};
																					""".format(team_id, match_type, timezone, sort_type, offset)

# ---> [TABLE teams]

# Получаем id команды по её названию 
query_select_teams_by_name = lambda team_name: "SELECT id, name, flag FROM teams WHERE name ILIKE '%{0}%'".format(team_name)

# Получаем id команды по её ТОЧНОМУ названию 
query_select_team_id_by_exact_name = lambda team_name: "SELECT id, name, flag FROM teams WHERE name = '{0}'".format(team_name)

# 
query_select_player_id_by_name = lambda player_name: "SELECT id, nik_name, name, flag FROM players WHERE nik_name ILIKE '%{0}%'".format(player_name)

# 
query_select_team_info = lambda team_id: "SELECT id, name, flag FROM teams WHERE id = {0}".format(team_id)

query_select_details_by_team = lambda team_id: "SELECT id, name, flag, number_maps, kd_diff, kd, rating_1_0 FROM teams WHERE id = {0}".format(team_id)

# 
query_select_teams_by_ids_array = lambda ids_array: """SELECT t.id, t.name, t.flag
														FROM unnest(ARRAY[{0}]) team_id
														LEFT JOIN teams t on t.id=team_id
														ORDER BY t.name
													""".format(ids_array)

# ---> [TABLE events]

# Получаем данные об ивентах по их типу (event_type) и сдвигаем выборку на определённое количество дней назад 
query_select_events_by_type = lambda event_type, offset_days: """SELECT id, name, start_date, stop_date 
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

query_select_event_by_team = lambda team_id: """SELECT id, name, start_date, stop_date 
												FROM events
												WHERE events.id IN 
													(SELECT distinct event_id FROM matches 
													WHERE (team1_id = {0} OR team2_id = {0}) 
														AND event_id NOTNULL)
												ORDER BY events.start_date
												""".format(team_id)

# Получаем информацию о событии по его id (event_id)
query_select_event_info = lambda event_id: """SELECT id, type, name, location, flag, start_date, stop_date, prize, count_teams 
												FROM events
												WHERE id = {0}""".format(event_id)

# Получаем id события по его названию
query_select_event_id_by_name = lambda event_name: "SELECT id FROM events WHERE name = '{0}'".format(event_name)

#
query_select_events_by_ids_array = lambda ids_array: """SELECT ev.id, ev.name
														FROM unnest(ARRAY[{0}]) event_id
														LEFT JOIN events ev on ev.id=event_id
														""".format(ids_array)

#
query_select_event_by_date = lambda date_: "SELECT id, name, start_date, stop_date FROM events WHERE to_char(start_date, 'MM.YYYY') = '{0}'".format(date_)


# ---> [TABLE news]

# Получаем данные о новостях
query_select_news = lambda offset: """SELECT id, news_text, flag, href 
													FROM news 
													ORDER BY news.day DESC 
													LIMIT {0};
												""".format(offset)

# 
query_select_news_by_date = lambda date_: """SELECT id, news_text, flag, href 
												FROM news 
												WHERE news.day = date '{0}'
												ORDER BY news.day DESC
											""".format(date_)

# 
query_select_news_notice = lambda offset: """WITH updated AS (UPDATE news SET notice = False)
															SELECT id, news_text, flag, href FROM news 
															WHERE notice
															ORDER BY news.day DESC 
															LIMIT {0};
														""".format(offset)

# ---> [TABLE players]

# 
query_select_player_info = lambda player_id: """SELECT id, nik_name, name, flag, number_maps, number_rounds, kd_diff, kd, rating_1_0 
												FROM players
												WHERE id = {0}""".format(player_id)



# INSERT ---------------------------------------------------------------------------------------------------------------

# ---> [TABLE telegram]

# Инсертим данные о новом пользователе
query_insert_new_user = "INSERT INTO telegram (id, language, name, joined) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING"


# ---> [TABLE matches]

# Инсертим данные о матчах
query_insert_matches = """INSERT INTO matches
							(id, type, unix_datetime, stars, lan, team1_id, team2_id, meta, event_id, result_score)
							VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
							ON CONFLICT (id) DO UPDATE
							SET (type, unix_datetime, team1_id, team2_id, meta, event_id, result_score)
							= (EXCLUDED.type, EXCLUDED.unix_datetime, EXCLUDED.team1_id, EXCLUDED.team2_id, EXCLUDED.meta, EXCLUDED.event_id, EXCLUDED.result_score)
							"""

# ---> [TABLE teams]

#
query_insert_teams = "INSERT INTO teams (id, name) VALUES (%s,%s) ON CONFLICT DO NOTHING"

# 
query_insert_stats_teams = """INSERT INTO teams 
								(id, name, flag, number_maps, kd_diff, kd, rating_1_0) 
								VALUES (%s,%s,%s,%s,%s,%s,%s)
								ON CONFLICT (id) DO UPDATE
								SET (flag, number_maps, kd_diff, kd, rating_1_0)
								= (EXCLUDED.flag, EXCLUDED.number_maps, EXCLUDED.kd_diff, EXCLUDED.kd, EXCLUDED.rating_1_0)"""

# ---> [TABLE players]

#
query_insert_stats_players = """INSERT INTO players 
										(id, team_id, nik_name, flag, number_maps, number_rounds, kd_diff, kd, rating_1_0) 
										VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
										ON CONFLICT (id) DO UPDATE
										SET (flag, number_maps, number_rounds, kd_diff, kd, rating_1_0)
										= (EXCLUDED.flag, EXCLUDED.number_maps, EXCLUDED.number_rounds, EXCLUDED.kd_diff, EXCLUDED.kd, EXCLUDED.rating)"""


# ---> [TABLE events]

# Инсертим данные о событиях
query_insert_events = """INSERT INTO events
						(id, type, name, location, flag, start_date, stop_date, prize, count_teams)
						VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) 
						ON CONFLICT (id) DO UPDATE
						SET (location, flag, start_date, stop_date, prize, count_teams)
						= (EXCLUDED.location, EXCLUDED.flag, EXCLUDED.start_date, EXCLUDED.stop_date, EXCLUDED.prize, EXCLUDED.count_teams)
						WHERE EXCLUDED.type NOTNULL
						"""


# ---> [TABLE news]

# Инсертим данные о новостях
query_insert_news = "INSERT INTO news (id, day, news_text, flag, href) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"



# UPDATE -----------------------------------------------------------------------------------------------------------

# ---> [TABLE telegram]

# Обновляем часовой пояс пользователя (timezone) по егo id (user_id)
query_update_user_timezone = lambda user_id, timezone: "UPDATE telegram SET timezone = '{1}' WHERE id = {0}".format(user_id, timezone)

# Обновляем данные о булевых значениях настроек по id пользователя (user_id) и названию параметра (colomn_name)
query_update_user_bool_parameter = lambda user_id, colomn_name:  "UPDATE telegram SET {1} = NOT telegram.{1} WHERE id = {0}".format(user_id, colomn_name)

# 
query_update_user_notice = lambda user_id, colomn_name, value, limit: """UPDATE telegram 
																		SET {1} = CASE
																			WHEN 
																				('{1}' IN ('notice_teams', 'notice_events') OR 
																				'{1}' = 'notice_matches' 
																				AND {2} = (SELECT matches.id FROM matches WHERE matches.id = {2}))
																				AND cardinality(ARRAY[{1}]) < {3} 
																				AND NOT ARRAY[{1}] @> ARRAY[{2}] 
																					THEN array_append({1}, {2}) 
																			ELSE array_remove({1}, {2}) 
																		END
																		WHERE telegram.id = {0} 
																		RETURNING {2} = ANY (ARRAY[{1}]), cardinality(ARRAY[{1}]) >= {3};
																	""".format(user_id, colomn_name, value, limit)

query_update_delete_old_events = """UPDATE telegram 
									SET notice_events = CASE 
										WHEN delete_old_events
										THEN ARRAY(SELECT unnest(notice_events)
											FROM telegram
											INTERSECT  
											SELECT id 
											FROM events 
											WHERE stop_date >= current_date)
										ELSE notice_events
									END;"""



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

	def user_data_by_colomn_names(self, user_id: int, colomn_names: list):
		query_select_user_data_by_colomn_names = lambda user_id, colomn_names: "SELECT {1} FROM telegram WHERE id = {0}".format(user_id, colomn_names)
		cursor.execute(query_select_user_data_by_colomn_names(user_id, ', '.join(colomn_names)))
		return [x for x in cursor.fetchone()]

	def notice(self, colomn_name: str, user_id: int, id_: int):
		cursor.execute(query_select_notice(user_id, id_, f"notice_{colomn_name}"))
		

		#print(cursor.fetchone())
		

		return not cursor.fetchone() is None

	def all_notice(self, user_id: int):
		cursor.execute(query_select_all_notice(user_id))
		return cursor.fetchone()

	def event_id_by_name(self, event_name: str):
		cursor.execute(query_select_event_id_by_name(event_name))
		return cursor.fetchone()[-1]

	# УЗНАТЬ, КАК МОЖНО ОПТИМИЗИРОВАТЬ ЭТОТ ЗАПРОС
	def teams_by_name(self, team_name: str, one_result = False):
		cursor.execute(query_select_teams_by_name(team_name))
		if one_result:
			return cursor.fetchone()
		return cursor.fetchall()

	def team_id_by_exact_name(self, team_name: str):
		cursor.execute(query_select_team_id_by_exact_name(team_name))
		return cursor.fetchone()

	def player_id_by_name(self, player_name: str, one_result = False):
		cursor.execute(query_select_player_id_by_name(player_name))
		if one_result:
			return cursor.fetchone()
		return cursor.fetchall()

	def matches(self, match_type: str, date_, timezone, stars_matches_display, type_sort = ''):
		if match_type == 'R':
			type_sort = 'DESC'
		cursor.execute(query_select_matches(match_type, date_, timezone, stars_matches_display, type_sort))
		return cursor.fetchall()

	def matches_by_ids_array(self, ids_array: list, timezone):
		cursor.execute(query_select_matches_by_ids_array(ids_array, timezone))
		return cursor.fetchall()

	def matches_by_event_id(self, event_id: int, timezone):
		cursor.execute(query_select_matches_by_event_id(event_id, timezone))
		return cursor.fetchall()

	def matches_by_team_id(self, team_id: int, match_type: str, timezone, sort_type = '', offset = 10):
		if match_type == 'R':
			sort_type = 'DESC'
		cursor.execute(query_select_matches_by_team_id(team_id, match_type, timezone, sort_type, offset))
		return cursor.fetchall()

	def match_info(self, match_id: int, timezone):
		cursor.execute(query_select_match_info(match_id, timezone))
		return cursor.fetchone()

	def team_info(self, team_id: int):
		cursor.execute(query_select_team_info(team_id))
		return cursor.fetchone()

	def details_by_team(self, team_id: int):
		cursor.execute(query_select_details_by_team(team_id))
		return cursor.fetchone()

	def teams_by_ids_array(self, ids_array):
		cursor.execute(query_select_teams_by_ids_array(ids_array))
		return cursor.fetchall()

	def live_matches(self):
		cursor.execute(query_select_live_matches)
		return cursor.fetchall()

	def live_matches_for_notice(self):
		cursor.execute(query_select_live_matches_for_notice)
		return cursor.fetchall()

	def user_ids_for_notice(self, match_id, team1_id, team2_id, event_id):
		cursor.execute(query_select_user_ids_for_notice(match_id, team1_id, team2_id, event_id))
		return [x[0] for x in cursor.fetchall()]

	def dates(self, user_timezone, match_type: str, comparison_sign = '>=', sort_type = '', count_days = 7):
		if match_type == 'R':
			comparison_sign = '<='
			sort_type = 'DESC'
		cursor.execute(query_select_dates(user_timezone, comparison_sign, sort_type, count_days))
		return cursor.fetchall()

	def events_by_type(self, event_type: str, offset_days = 3):
		if event_type == 'O':
			cursor.execute(query_select_events_by_type_ongoing)
		else:
			cursor.execute(query_select_events_by_type(event_type, offset_days))
		return cursor.fetchall()

	def events_by_ids_array(self, ids_array):
		cursor.execute(query_select_events_by_ids_array(ids_array))
		return cursor.fetchall()

	def event_info(self, event_id: int):
		cursor.execute(query_select_event_info(event_id))
		return cursor.fetchone()

	def news(self, date_ = None, notice = None, offset_news = 10, offset_news_notice = 5):
		if not date_ is None:
			cursor.execute(query_select_news_by_date(date_))
		elif not notice is None:
			cursor.execute(query_select_news_notice(offset_news_notice))
		else:
			cursor.execute(query_select_news(offset_news))
		return cursor.fetchall()

	def user_ids_for_news_notice(self):
		cursor.execute(query_select_user_ids_for_news_notice)
		return [x[0] for x in cursor.fetchall()]

	def blocked_user_ids(self):
		cursor.execute(query_select_blocked_users)
		return [x[0] for x in cursor.fetchall()]

	def events_by_team(self, team_id: int):
		cursor.execute(query_select_event_by_team(team_id))
		return cursor.fetchall()

	def events_by_date(self, date_):
		cursor.execute(query_select_event_by_date(date_))
		return cursor.fetchall()

	def player_info(self, player_id: int):
		cursor.execute(query_select_player_info(player_id))
		return cursor.fetchone()


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

	def stats_teams(self, stats_teams_array):
		cursor.executemany(query_insert_stats_teams, stats_teams_array)
		connection.commit()

	def stats_players(self, stats_players_array):
		cursor.executemany(query_insert_stats_players, stats_players_array)
		connection.commit()



class UPDATE:
	
	def user_timezone(self, user_id: int, timezone):
		cursor.execute(query_update_user_timezone(user_id, timezone))
		connection.commit()

	def user_bool_parameter(self, user_id: int, colomn_name: str):
		cursor.execute(query_update_user_bool_parameter(user_id, colomn_name))
		connection.commit()

	def user_notice(self, user_id, type_notice, id_, limit = 20):
		colomn_name = 'notice_' + type_notice
		cursor.execute(query_update_user_notice(user_id, colomn_name, id_, limit))
		connection.commit()
		update_result, limit_condition = cursor.fetchone()
		return update_result, not update_result and limit_condition

	def delete_old_events(self):
		cursor.execute(query_update_delete_old_events)
		connection.commit()
	
	def stars_matches_display(self, user_id: int):
		query_update_stars_matches_display = """UPDATE telegram 
													SET stars_matches_display = CASE 
													WHEN stars_matches_display < 5
														THEN stars_matches_display + 1
													ELSE 0
													END
												WHERE telegram.id = {0}
												""".format(user_id)
		cursor.execute(query_update_stars_matches_display)
		connection.commit()



class DELETE:

	def table(self, tableName: str):
		cursor.execute(f"DROP TABLE {tableName} IF EXISTS")
		connection.commit()

	def one_row(self, tableName: str, id_: int):
		cursor.execute(f"DELETE FROM {tableName} WHERE id = {id_}")
		connection.commit()

	def rows(self, tableName: str):
		cursor.execute(f"DELETE FROM {tableName}")
		connection.commit()



class TABLE:

	def your_request(self, query):
		cursor.execute(query)
		connection.commit()

	def telegram(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS telegram (
							id integer NOT NULL PRIMARY KEY,
							language varchar (4) DEFAULT 'en',
							name text,
							joined date,
							ban boolean,
							timezone interval DEFAULT '00:00:00'::interval,
							notice_teams integer[],
							notice_matches integer[],
							notice_events integer[],
							receive_notices boolean DEFAULT True,
							news_notice boolean DEFAULT True,
							delete_old_events boolean DEFAULT False,
							delete_old_matches boolean DEFAULT True,
							stars_matches_display smallint DEFAULT 0
						);""")
		connection.commit()

	def events(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS events (
							id integer NOT NULL PRIMARY KEY,
							type varchar (1),
							name text,
							location text,
							flag varchar (7),
							start_date date,
							stop_date date,
							prize integer,
							count_teams smallint
						);""")
		connection.commit()

	def matches(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS matches (
							id integer NOT NULL PRIMARY KEY,
							notice boolean DEFAULT True,
							type varchar (1),
							unix_datetime timestamp without time zone,
							stars smallint,
							lan boolean,
							team1_id smallint REFERENCES teams (id),
							team2_id smallint REFERENCES teams (id),
							meta text,
							event_id integer REFERENCES events (id),
							result_score integer[] 
						);""")
		connection.commit()

	def teams(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS teams (
							id integer NOT NULL PRIMARY KEY,
							name text NOT NULL,
							flag varchar (7),
							number_maps integer,
							kd_diff integer,
							kd real,
							rating_1_0 real
						);""")
		connection.commit()

	def players(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS players (
							id integer NOT NULL PRIMARY KEY,
							team_id smallint REFERENCES teams (id),
							nik_name text NOT NULL,
							name text,
							flag varchar (7),
							number_maps integer,
							number_rounds integer,
							kd_diff integer,
							kd real,
							rating_1_0 real
						);""")
		connection.commit()

	def news(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS news (
							id integer NOT NULL PRIMARY KEY,
							notice boolean DEFAULT True,
							day date,
							news_text text,
							flag varchar (7),
							href text
						);""")
		connection.commit()

	def stat(self):
		cursor.execute("""CREATE TABLE IF NOT EXISTS stat (
							day date NOT NULL PRIMARY KEY,
							count_text integer,
							count_callback integer
						);""")
		connection.commit()

	

def CreateDatabase():
	database_name = 'hltv'
	cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
	connection.commit()




def check_exists_tables():
	TABLE().telegram()

	TABLE().events()

	TABLE().teams()
	TABLE().players()
	TABLE().matches()
	
	TABLE().news()

	TABLE().stat()




def CONNECT(db_settings: dict):
	global connection
	global cursor

	connection = psycopg2.connect(**db_settings)
	connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
	cursor = connection.cursor()

	cursor.execute("SELECT version();")
	record = cursor.fetchone()
	print(record, "\n")

	check_exists_tables()

	return TABLE(), INSERT(), UPDATE(), SELECT(), DELETE()


'''
ускоряет выполнение запроса при больших объёмах

#args_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", x) for x in matches_object)
#cur.execute("INSERT INTO matches VALUES " + args_str)
#connection.commit()

'''