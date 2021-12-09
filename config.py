db_settings = {
                'user': "postgres",
                'password': "YOUR_PASSWORD",
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


TOKEN = "YOUR_TOKEN"


# webhook settings
WEBHOOK_HOST = ''
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '127.0.0.1'  # or ip
WEBAPP_PORT = 5000
