
<h1 align="center">HLTV Bot</h1>

<p align="center">
<img src="https://img.shields.io/github/stars/nik20z/hltv_bot">
<img src="https://img.shields.io/github/issues/nik20z/hltv_bot">
<img src="https://img.shields.io/github/license/nik20z/hltv_bot">
</p>

## Description

[Telegram Bot](https://t.me/hltv_analytics_bot "hltv_bot") is designed for convenient viewing of information about matches and events in the world of CS: GO
Information is taken from this [site](hltv.org "hltv.org") 


## Implementation features

The main advantages of a bot from a developer's point of view, in my opinion, are:

1. Using the asynchronous library aiogram
2. Complete database postgreSQL
3. The ability to select a time zone, so each user receives personalized information about matches (it is also possible to send his geolocation and the bot will set the time zone itself)
4. Antiflood system
5. Each message can work on its own, i.e. the buttons contain information about the previous states, thus, even after a while, the bot will correctly return the user to the previous step



## Bot capabilities

/settings - settings menu
/today - today's matches
/tomorrow - tomorrow's matches
/live - live broadcast
/results_today - today's results
/matches {date} - matches for a specific day
/results {date} - results for a specific day
/events - events info
/news - latest news
/keyboard - show keyboard
