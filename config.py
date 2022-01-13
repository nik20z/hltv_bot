db_settings = {
                'user': "user_name",
                'password': "password",
                'host': "localhost",
                'port': 5432, 
                'database': 'hltv'
}

log_settings = {
                'sink': "log/info.log",
                'format': "[{time:%H:%M:%S}] {level} {message} {exception}",
                'level': "DEBUG",
                'rotation': "00:00",
                'compression': "zip"    
}



interval_hours = lambda hour: 3600*hour
interval_minutes = lambda minute: 60*minute

DEFAULT_INTERVAL_UPDATE = interval_hours(1)

Intervals_parse = {
    'events': interval_hours(24),
    'news': interval_hours(3),
    'matches': interval_hours(2)
}

Intervals = lambda func_name: {
                                'LiveNotifications': Intervals_parse['matches'],
                                'NewsNotifications': Intervals_parse['news'],
                                'DeleteOldEvents': interval_hours(24)
}.get(func_name, DEFAULT_INTERVAL_UPDATE)



TOKEN = ""


# webhook settings
WEBHOOK_HOST = 'https://16b5-5-167-46-228.ngrok.io'
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '127.0.0.1'  # or ip
WEBAPP_PORT = 5000
