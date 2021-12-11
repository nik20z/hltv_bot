
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


- /settings - settings menu
 
  <img src="https://user-images.githubusercontent.com/62090150/145673843-06da82a0-685e-4442-a76f-a95b14741333.png" width="30%"></p>

- /today - today's matches
  
  <img src="https://user-images.githubusercontent.com/62090150/145673886-90bbcbc3-665d-447a-a395-444657e6c027.png" width="30%"></p>
  <img src="https://user-images.githubusercontent.com/62090150/145674029-041b89ba-fdc9-472e-bc4e-0ff6f803b319.png" width="30%"></p>

- /tomorrow - tomorrow's matches
- /live - live broadcast
- /results_today - today's results
  
  <img src="https://user-images.githubusercontent.com/62090150/145674082-a13870d3-fc23-4186-b343-fa352191810b.png" width="30%"></p>
  <img src="https://user-images.githubusercontent.com/62090150/145674112-8eb6e62f-0756-4aa1-a064-332f8d73d7f9.png" width="30%"></p>

  
- /matches {date} - matches for a specific day
  
  <img src="https://user-images.githubusercontent.com/62090150/145673959-a775d45f-9b4b-4048-94ea-c1593b39bdd4.png" width="30%"></p>
  
- /results {date} - results for a specific day
- /events - events info

  <img src="https://user-images.githubusercontent.com/62090150/145673930-8c55d5d6-cd36-4871-8ad2-2225eb67495f.png" width="30%"></p>
  <img src="https://user-images.githubusercontent.com/62090150/145673979-baf2dbec-90c7-4b4b-bce3-a84993496c11.png" width="30%"></p>
  <img src="https://user-images.githubusercontent.com/62090150/145673994-c5f38799-2153-426b-96c5-eca64e2bb710.png" width="30%"></p>
  <img src="https://user-images.githubusercontent.com/62090150/145674008-ff00f1e2-2ce9-43d5-aa15-4eac4f05cd55.png" width="30%"></p>
  
- /news - latest news
 
  <img src="https://user-images.githubusercontent.com/62090150/145674158-54da6b5e-8d76-46d5-a6d9-c2138288e16e.png" width="30%"></p>
 
- /keyboard - show keyboard
