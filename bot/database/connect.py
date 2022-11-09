import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
# from psycopg2.extras import LoggingConnection, LoggingCursor

from bot.misc import DataBase


connection = psycopg2.connect(**DataBase.SETTINGS)
connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
connection.set_client_encoding('UTF8')
cursor = connection.cursor()
