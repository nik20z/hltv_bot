MAIN_URL = 'https://www.hltv.org/'
PART_LINKS = {"events": "events#tab-ALL",
				"matches": "matches",
				"results": "results",
				"news": lambda year, month: f"/news/archive/{year}/{month}",
				"stats_teams": "stats/teams?minMapCount=0",
				"stats_players": "stats/players?minMapCount=0"
				}
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203 (Edition Campaign 34)'
			}




