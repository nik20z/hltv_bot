from bot.database.connect import cursor, connection


def user_info(user_id=None):
    """Получаем всю информацию о пользователе"""
    if user_id is None:
        cursor.execute("SELECT user_id FROM telegram")
        return [x[0] for x in cursor.fetchall()]

    query = "SELECT * FROM telegram WHERE user_id = {0}".format(user_id)
    cursor.execute(query)
    return cursor.fetchone()


def user_settings(user_id: int):
    # Получаем настройки пользователя (timezone, live_notification) по его id
    query = """SELECT timezone_, 
                    receive_notices, 
                    news_notice, 
                    delete_old_matches, 
                    delete_old_events, 
                    stars_matches_display
               FROM telegram
               WHERE user_id = {0}""".format(user_id)
    cursor.execute(query)
    return cursor.fetchone()


def user_data_by_colomn_names(user_id: int, colomn_names: list):
    query = "SELECT {1} FROM telegram WHERE user_id = {0}".format(user_id, ', '.join(colomn_names))
    cursor.execute(query)
    return [x for x in cursor.fetchone()]


def notice(colomn_name: str, user_id: int, id_: int):
    query = """SELECT 1 FROM telegram WHERE user_id = {0} AND {1} = ANY ({2});""".format(user_id, id_, f"notice_{colomn_name}")
    cursor.execute(query)

    # print(cursor.fetchone())

    return not cursor.fetchone() is None


def all_notice(user_id: int):
    query = """SELECT 'teams', notice_teams, 'matches', notice_matches, 'events', notice_events 
                FROM telegram 
                WHERE user_id = {0}""".format(user_id)
    cursor.execute(query)
    return cursor.fetchone()


def event_id_by_name(event_name: str):
    """Получаем id события по его названию"""
    query = "SELECT event_id FROM event WHERE event_name = '{0}'".format(event_name)
    cursor.execute(query)
    return cursor.fetchone()[-1]


# УЗНАТЬ, КАК МОЖНО ОПТИМИЗИРОВАТЬ ЭТОТ ЗАПРОС
def teams_by_name(team_name: str, one_result = False):
    """Получаем id команды по её названию"""
    query = "SELECT team_id, team_name, flag FROM team WHERE team_name ILIKE '%{0}%'".format(team_name)
    cursor.execute(query)
    if one_result:
        return cursor.fetchone()
    return cursor.fetchall()


def team_id_by_exact_name(team_name: str):
    """Получаем id команды по её ТОЧНОМУ названию"""
    query = "SELECT team_id, team_name, flag FROM team WHERE team_name = '{0}'".format(team_name)
    cursor.execute(query)
    return cursor.fetchone()


def player_id_by_name(player_name: str, one_result = False):
    query = "SELECT player_id, nik_name, player_name, flag FROM player WHERE nik_name ILIKE '%{0}%'".format(player_name)
    cursor.execute(query)
    if one_result:
        return cursor.fetchone()
    return cursor.fetchall()

def matches(match_type: str, date_, timezone, stars_matches_display, type_sort = ''):
    """Получаем матчи с учётом их типа (match_type), даты (date_) и часового пояса (timezone) пользователя"""
    if match_type == 'R':
        type_sort = 'DESC'
    query = """SELECT match.match_id, 
                      match.match_type, 
                      to_char(unix_datetime::time + interval '{2}', 'HH24:MI'), 
                      tm1.team_name, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score 
                FROM match
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id) 
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE match.match_type = '{0}' 
                    AND (unix_datetime + interval '{2}')::date = date '{1}' 
                    AND match.stars >= {3} 
                    AND tm2.team_name NOTNULL
                ORDER BY unix_datetime {4};
                """.format(match_type, date_, timezone, stars_matches_display, type_sort)
    print("query", query)
    cursor.execute(query)
    return cursor.fetchall()

def matches_by_ids_array(ids_array: list, timezone):
    query = """SELECT m.match_id, 
                      m.match_type, 
                      to_char(unix_datetime + interval '{1}', 'DD Mon HH24:MI'), 
                      tm1.team_name, 
                      tm2.team_name, 
                      m.event_id, 
                      ev.event_name, 
                      result_score
                FROM unnest(ARRAY[{0}]) mch_id
                LEFT JOIN match m on m.match_id = mch_id
                LEFT JOIN team as tm1 ON (m.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (m.team2_id = tm2.team_id)
                LEFT JOIN event as ev ON (m.event_id = ev.event_id) 
                ORDER BY unix_datetime DESC
                """.format(ids_array, timezone)
    cursor.execute(query)
    return cursor.fetchall()

def matches_by_event_id(event_id: int, timezone):
    # Получаем матчи с учётом их принадлежности к конкретному событию (event_id) И сразу же вносим правку на часовой пояс пользоватя (timezone)
    query = """SELECT match.match_id, 
                      match.match_type, 
                      to_char(unix_datetime + interval '{1}', 'DD Mon HH24:MI'), 
                      tm1.team_name, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score 
                FROM match
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id)
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE match.event_id = {0} AND tm2.team_name NOTNULL
                ORDER BY unix_datetime;
                """.format(event_id, timezone)
    cursor.execute(query)
    return cursor.fetchall()

def matches_by_team_id(team_id: int, match_type: str, timezone, sort_type = '', offset = 10):
    if match_type == 'R':
        sort_type = 'DESC'
    query = """SELECT match.match_id,
                      match.match_type, 
                      to_char(unix_datetime + interval '{2}', 'DD Mon HH24:MI'), 
                      tm1.team_name, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score 
                FROM match 
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id) 
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE (match.match_type = '{1}' OR match.match_type = 'L')
                AND (tm1.team_id = {0} OR tm2.team_id = {0})
                AND tm2.team_name NOTNULL
                ORDER BY unix_datetime {3}
                LIMIT {4};
                """.format(team_id, match_type, timezone, sort_type, offset)
    cursor.execute(query)
    return cursor.fetchall()

def match_info(match_id: int, timezone):
    """Получаем информацию о матче по его id (scorebot_id) и сразу же вносим правку на часовой пояс (timezone) пользователя"""
    query = """SELECT match.match_id, 
                      match.match_type, 
                      to_char(unix_datetime + interval '{1}', 'HH24:MI (DD Mon)'), 
                      stars, 
                      meta, 
                      tm1.team_id, 
                      tm1.team_name, 
                      tm2.team_id, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score 
                FROM match
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id)
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE match.match_id = {0};
                """.format(match_id, timezone)
    cursor.execute(query)
    return cursor.fetchone()

def team_info(team_id: int):
    query = "SELECT team_id, team_name, flag FROM team WHERE team_id = {0}".format(team_id)
    cursor.execute(query)
    return cursor.fetchone()

def details_by_team_id(team_id: int):
    query = "SELECT team_id, team_name, flag, number_maps, kd_diff, kd, rating_1_0 FROM team WHERE team_id = {0}".format(team_id)
    cursor.execute(query)
    return cursor.fetchone()

def players_by_team_id(team_id: int):
    query = """SELECT player.player_id, nik_name, player.player_name, player.flag, t.team_id, t.team_name, t.flag 
                FROM player
                LEFT JOIN team as t ON (player.team_id = t.team_id)
                WHERE player.team_id = {0}
                """.format(team_id)
    cursor.execute(query)
    return cursor.fetchall()

def teams_by_ids_array(ids_array):
    query = """SELECT t.team_id, t.team_name, t.flag
                FROM unnest(ARRAY[{0}]) tm_id
                LEFT JOIN team t on t.team_id=tm_id
                ORDER BY t.team_name
                """.format(ids_array)
    cursor.execute(query)
    return cursor.fetchall()

def live_matches():
    """Получаем данные о прямых трансляциях"""
    query = """SELECT match.match_id,
                      match.match_type, 
                      unix_datetime, 
                      tm1.team_name, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score 
                FROM match
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id) 
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE match.match_type = 'L'
                """
    cursor.execute(query)
    return cursor.fetchall()

def live_matches_for_notice():
    query = """SELECT match.match_id, 
                      stars, 
                      team1_id, 
                      tm1.team_name, 
                      team2_id, 
                      tm2.team_name, 
                      match.event_id, 
                      ev.event_name, 
                      result_score
                FROM match
                LEFT JOIN team as tm1 ON (match.team1_id = tm1.team_id) 
                LEFT JOIN team as tm2 ON (match.team2_id = tm2.team_id) 
                LEFT JOIN event as ev ON (match.event_id = ev.event_id) 
                WHERE match.match_type = 'L'"""
    cursor.execute(query)
    return cursor.fetchall()

def user_ids_for_notice(match_id: int, team1_id: int, team2_id: int, event_id: int):
    query = """WITH updated AS (UPDATE telegram SET notice_matches = CASE
                        WHEN user_id = telegram.user_id AND telegram.delete_old_matches 
                            THEN array_remove(notice_matches, {0})
                        ELSE notice_matches
                        END)
                SELECT user_id FROM telegram 
                WHERE telegram.receive_notices AND 
                    ({0} = ANY (notice_matches) OR 
                    {1} = ANY (notice_teams) OR
                    {2} = ANY (notice_teams) OR
                    {3} = ANY (notice_events));
                """.format(match_id,
                           team1_id,
                           team2_id,
                           event_id)
    cursor.execute(query)
    return [x[0] for x in cursor.fetchall()]

def dates(user_timezone, match_type: str, comparison_sign = '>=', sort_type = '', count_days = 7):
    """Получаем массив дат с учётом часового пояса (user_timezone), напрвления отбора (comparison_sign - больше-равно или меньше-равно), количества дней (count_days) и сдвига (offset_days)"""
    if match_type == 'R':
        comparison_sign = '<='
        sort_type = 'DESC'
    query = """SELECT distinct (unix_datetime + interval '{0}')::date AS date_
                FROM match
                WHERE (unix_datetime + interval '{0}')::date {1} current_date
                ORDER BY date_ {2}
                LIMIT {3};
                """.format(user_timezone,
                           comparison_sign,
                           sort_type,
                           count_days)
    cursor.execute(query)
    return cursor.fetchall()

def events_by_type(event_type: str, offset_days = 3):
    if event_type == 'O':
        # Получаем данные о текущих событиях (на основе start_date и stop_date)
        query= """SELECT event_id, event_name, start_date, stop_date 
                    FROM event
                    WHERE event.start_date <= current_date 
                        AND event.stop_date >= current_date
                    ORDER BY event.start_date;
                    """
        cursor.execute(query)
    else:
        # Получаем данные о текущих событиях (на основе start_date и stop_date)
        query = """SELECT event_id, event_name, start_date, stop_date 
                    FROM event
                    WHERE event_type = '{0}' 
                        AND event.stop_date > current_date - interval '{1} days'
                    ORDER BY event.start_date;
                    """.format(event_type, offset_days)
        cursor.execute(query)
    return cursor.fetchall()

def events_by_ids_array(ids_array):
    query = """SELECT ev.event_id, ev.event_name
                FROM unnest(ARRAY[{0}]) ev_id
                LEFT JOIN event ev on ev.event_id=ev_id
                """.format(ids_array)
    cursor.execute(query)
    return cursor.fetchall()

def event_info(event_id: int):
    """Получаем информацию о событии по его id (event_id)"""
    query = """SELECT event_id, event_type, event_name, location_, flag, start_date, stop_date, prize, count_teams 
                FROM event
                WHERE event_id = {0}""".format(event_id)
    cursor.execute(query)
    return cursor.fetchone()

def news(date_ = None, notice = None, offset_news = 10, offset_news_notice = 5):
    if not date_ is None:
        query = """SELECT news_id, news_text, flag, href 
                    FROM news 
                    WHERE news.day_ = date '{0}'
                    ORDER BY news.day_ DESC
                    """.format(date_)
        cursor.execute(query)
    elif not notice is None:
        query = """WITH updated AS (UPDATE news SET notice_ = False)
                    SELECT news_id, news_text, flag, href 
                    FROM news 
                    WHERE notice_
                    ORDER BY news.day_ DESC 
                    LIMIT {0};
                    """.format(offset_news_notice)
        cursor.execute(query)
    else:
        """Получаем данные о новостях"""
        query = """SELECT news_id, news_text, flag, href 
                    FROM news 
                    ORDER BY news.day_ DESC 
                    LIMIT {0};
                    """.format(offset_news)
        cursor.execute(query)
    return cursor.fetchall()

def user_ids_for_news_notice():
    query = "SELECT user_id FROM telegram WHERE news_notice"
    cursor.execute(query)
    return [x[0] for x in cursor.fetchall()]

def blocked_user_ids():
    """Получаем массив id закбокированнных пользователей"""
    query = "SELECT user_id FROM telegram WHERE ban"
    cursor.execute(query)
    return [x[0] for x in cursor.fetchall()]

def events_by_team(team_id: int, offset = 10):
    query = """SELECT event_id, event_name, start_date, stop_date 
                FROM event
                WHERE event.event_id IN 
                    (SELECT distinct event_id FROM match 
                    WHERE (team1_id = {0} OR team2_id = {0}) 
                        AND event_id NOTNULL)
                ORDER BY event.start_date
                LIMIT {1}
                """.format(team_id, offset)
    cursor.execute(query)
    return cursor.fetchall()

def events_by_date(date_):
    query = """SELECT event_id, event_name, start_date, stop_date 
                FROM event 
                WHERE to_char(start_date, 'MM.YYYY') = '{0}'
                """.format(date_)
    cursor.execute(query)
    return cursor.fetchall()

def player_info_by_id(player_id: int):
    query = """SELECT player.player_id, 
                      t.team_id, 
                      t.team_name, 
                      t.flag, 
                      nik_name, 
                      player.player_name, 
                      player.flag, 
                      player.number_maps, 
                      player.number_rounds, 
                      player.kd_diff, 
                      player.kd, 
                      player.rating_1_0 
                FROM player
                LEFT JOIN team as t ON (player.team_id = t.team_id)
                WHERE player.player_id = {0}
                """.format(player_id)
    cursor.execute(query)
    return cursor.fetchone()

