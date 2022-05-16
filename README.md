
<h1 align="center">HLTV Bot</h1>

<p align="center">
<img src="https://img.shields.io/github/stars/nik20z/hltv_bot">
<img src="https://img.shields.io/github/issues/nik20z/hltv_bot">
<img src="https://img.shields.io/github/license/nik20z/hltv_bot">
</p>

## Description

[Telegram Bot](https://t.me/hltv_analytics_bot "hltv_bot") is designed for convenient viewing of information about matches and events in the world of CS: GO
Information is taken from this [site](https://www.hltv.org "hltv.org") 


## Implementation features

The main advantages of a bot from a developer's point of view, in my opinion, are:

1. Using the asynchronous library aiogram
2. Complete database postgreSQL
3. The ability to select a time zone, so each user receives personalized information about matches (it is also possible to send his geolocation and the bot will set the time zone itself)
4. Antiflood system
5. Each message can work on its own, i.e. the buttons contain information about the previous states, thus, even after a while, the bot will correctly return the user to the previous step



## Bot capabilities

```
/settings - settings menu
/today - today's matches
/tomorrow - tomorrow's matches
/live - live broadcasts
/results_today - today's results
/events - events information
/news - latest news
/matches - weekly matches
/results - weekly results
/keyboard - show keyboard
/notifications - list of notification subscriptions

Date picker:
mathces {date} - matches for a specific day
results {date} - results
news {date} - news
search team {team_name} - team search
search player {player_name} - player search
```

## Future updates:

- [ ] Improving anti-flood system that can effectively block spammers


## Installation order:

```
sudo apt update
sudo apt install python3.8
sudo apt install python3-pip

sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -i -u postgres
  psql
    CREATE USER hltv WITH PASSWORD 'your_password';
    CREATE DATABASE hltv;

pip3 install aiohttp
pip3 install beautifulsoup4
pip3 install pytz
pip3 install loguru
pip3 install timezonefinder
pip3 install aiogram
pip3 install psycopg2-binary
pip3 install lxml
```




