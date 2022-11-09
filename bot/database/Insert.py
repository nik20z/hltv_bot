from bot.database.connect import cursor, connection


def new_user(new_user_data: tuple):
    """Инсертим данные о новом пользователе"""
    query = "INSERT INTO telegram (user_id, language_, user_name, joined) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING"
    cursor.execute(query, new_user_data)


def matches(matches_data: tuple):
    """Инсертим данные о матчах"""
    query = """INSERT INTO match
                    (match_id, 
                    match_type, 
                    unix_datetime, 
                    stars, 
                    lan, 
                    team1_id, 
                    team2_id, 
                    meta, 
                    event_id, 
                    result_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (match_id) DO UPDATE
                SET (match_type, unix_datetime, team1_id, team2_id, meta, event_id, result_score)
                = (EXCLUDED.match_type, 
                    EXCLUDED.unix_datetime, 
                    EXCLUDED.team1_id, 
                    EXCLUDED.team2_id, 
                    EXCLUDED.meta, 
                    EXCLUDED.event_id, 
                    EXCLUDED.result_score)
                """
    cursor.executemany(query, matches_data)
    connection.commit()

def teams(teams_data: tuple):
    query = "INSERT INTO team (team_id, team_name) VALUES (%s,%s) ON CONFLICT DO NOTHING"
    cursor.executemany(query, teams_data)
    connection.commit()

def events(events_data: tuple):
    """Инсертим данные о событиях"""
    query = """INSERT INTO event
    						(event_id, 
    						event_type, 
    						event_name, 
    						location_, 
    						flag, 
    						start_date,
    						stop_date, 
    						prize, 
    						count_teams)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                ON CONFLICT (event_id) DO UPDATE
                SET (location_, flag, start_date, stop_date, prize, count_teams)
                = (EXCLUDED.location_, 
                    EXCLUDED.flag, 
                    EXCLUDED.start_date, 
                    EXCLUDED.stop_date, 
                    EXCLUDED.prize, 
                    EXCLUDED.count_teams)
                WHERE EXCLUDED.event_type NOTNULL
                """
    cursor.executemany(query, events_data)
    connection.commit()

def news(news_data: tuple):
    """Инсертим данные о новостях"""
    query = "INSERT INTO news (news_id, day_, news_text, flag, href) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING"
    cursor.executemany(query, news_data)
    connection.commit()

def stats_teams(stats_teams_array):
    query = """INSERT INTO team 
                (team_id, team_name, flag, number_maps, kd_diff, kd, rating_1_0) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (team_id) DO UPDATE
                SET (flag, number_maps, kd_diff, kd, rating_1_0)
                = (EXCLUDED.flag, 
                    EXCLUDED.number_maps, 
                    EXCLUDED.kd_diff, 
                    EXCLUDED.kd, 
                    EXCLUDED.rating_1_0)
                """
    cursor.executemany(query, stats_teams_array)
    connection.commit()

def stats_players(stats_players_array):
    query = """INSERT INTO player
                (player_id, team_id, nik_name, flag, number_maps, number_rounds, kd_diff, kd, rating_1_0) 
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (player_id) DO UPDATE
                SET (flag, number_maps, number_rounds, kd_diff, kd, rating_1_0)
                = (EXCLUDED.flag, 
                    EXCLUDED.number_maps, 
                    EXCLUDED.number_rounds, 
                    EXCLUDED.kd_diff, 
                    EXCLUDED.kd, 
                    EXCLUDED.rating_1_0)
                """
    cursor.executemany(query, stats_players_array)
    connection.commit()