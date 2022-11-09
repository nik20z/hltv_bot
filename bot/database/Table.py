from bot.database.connect import cursor, connection


view_create_queries = {}


table_create_queries = {"telegram": """CREATE TABLE IF NOT EXISTS telegram (
                                                            user_id integer NOT NULL PRIMARY KEY,
                                                            language_ varchar (4) DEFAULT 'en',
                                                            user_name text,
                                                            joined date,
                                                            ban boolean,
                                                            timezone_ interval DEFAULT '00:00:00'::interval,
                                                            notice_teams integer[],
                                                            notice_matches integer[],
                                                            notice_events integer[],
                                                            receive_notices boolean DEFAULT True,
                                                            news_notice boolean DEFAULT True,
                                                            delete_old_events boolean DEFAULT False,
                                                            delete_old_matches boolean DEFAULT True,
                                                            stars_matches_display smallint DEFAULT 0);""",

                        "event": """CREATE TABLE IF NOT EXISTS event (
                                                            event_id integer NOT NULL PRIMARY KEY,
                                                            event_type varchar (1),
                                                            event_name text,
                                                            location_ text,
                                                            flag varchar (7),
                                                            start_date date,
                                                            stop_date date,
                                                            prize integer,
                                                            count_teams smallint);""",

                        "team": """CREATE TABLE IF NOT EXISTS team (
                                                            team_id integer NOT NULL PRIMARY KEY,
                                                            team_name text NOT NULL,
                                                            flag varchar (7),
                                                            number_maps integer,
                                                            kd_diff integer,
                                                            kd real,
                                                            rating_1_0 real);""",
                        
                        "match": """CREATE TABLE IF NOT EXISTS match (
                                                            match_id integer NOT NULL PRIMARY KEY,
                                                            notice_ boolean DEFAULT True,
                                                            match_type varchar (1),
                                                            unix_datetime timestamp without time zone,
                                                            stars smallint,
                                                            lan boolean,
                                                            team1_id smallint REFERENCES team (team_id),
                                                            team2_id smallint REFERENCES team (team_id),
                                                            meta text,
                                                            event_id integer REFERENCES event (event_id),
                                                            result_score integer[]);""",
                        
                        "player": """CREATE TABLE IF NOT EXISTS player (
                                                            player_id integer NOT NULL PRIMARY KEY,
                                                            team_id smallint REFERENCES team (team_id),
                                                            nik_name text NOT NULL,
                                                            player_name text,
                                                            flag varchar (7),
                                                            number_maps integer,
                                                            number_rounds integer,
                                                            kd_diff integer,
                                                            kd real,
                                                            rating_1_0 real);""",

                        "news": """CREATE TABLE IF NOT EXISTS news (
                                                            news_id integer NOT NULL PRIMARY KEY,
                                                            notice_ boolean DEFAULT True,
                                                            day_ date,
                                                            news_text text,
                                                            flag varchar (7),
                                                            href text);""",

                        "stat": """CREATE TABLE IF NOT EXISTS stat (
                                                            day_ date NOT NULL PRIMARY KEY,
                                                            count_text integer,
                                                            count_callback integer);"""
                        }


def drop(table_name=None, cascade_state=False):
    """Удаляем таблицу"""
    if table_name is None:
        for table_name in table_create_queries.keys():
            drop(table_name)
    cascade = "CASCADE" if cascade_state else ""
    cursor.execute(f"DROP TABLE IF EXISTS {table_name} {cascade};")
    connection.commit()


def create(table_name=None):
    """Создаём таблицу"""
    if table_name is None:
        for table_name in table_create_queries.keys():
            create(table_name=table_name)
    else:
        cursor.execute(table_create_queries.get(table_name, None))
        connection.commit()


def create_view(view_name=None):
    """Создаём представление"""
    if view_name is None:
        for view_name in view_create_queries.keys():
            create_view(view_name=view_name)
    else:
        cursor.execute(view_create_queries.get(view_name, None))
        connection.commit()


def delete(table_name=None):
    if table_name is None:
        for table_name in table_create_queries.keys():
            delete(table_name)
    else:
        cursor.execute(f"DELETE FROM {table_name};")
        connection.commit()
