import datetime
import json
import requests
import time

from pprint import pprint
from bs4 import BeautifulSoup


# config
#["matches", "results", "events"]

URL = 'https://www.hltv.org/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.203 (Edition Campaign 34)'
			}


def no_except(function):
	def wrapper(*args, **kwargs):
		try:
			return_function = function(*args, **kwargs)
		except:
			return_function = None
		return return_function
	return wrapper




class MatchData:
	def __init__(self, match_soup):
		self.match_soup = match_soup
		self.href_split = self.match_soup.find('a')['href'].split('/')

	def get(self, matchType):
		data = [self.scorebot_ID(), # integer
				matchType, # char(1)
				self.matchTime_Unix(), # timestamp without time zone 
				self.stars(), # smallint
				self.lan(), # boolean
				self.team_ID(1), # smallint
				self.team_ID(2), # smallint
				self.matchTeamName(),
				#self.href(), # text
				self.matchMeta(), # varchar(5)
				self.get_event_ID(self.matchEventName()), # smallint
				self.resultScore() # integer[]
				]

		return data


	def get_team_ID(self, matchTeamName):
		pass

	def get_event_ID(self, matchEventName):
		'''
		чекаем в БД наличие ивента
		если его нет, то парсим ивенты и опять чекаем
		возвращаем ID
		'''
		return matchEventName


	def scorebot_ID(self):
		return int(self.href_split[2])

	@no_except
	def matchTime_Unix(self):
		matchTime_Unix_str = self.match_soup['data-zonedgrouping-entry-unix']
		matchTime_Unix_int = int(matchTime_Unix_str)/1000
		return datetime.datetime.utcfromtimestamp(matchTime_Unix_int)

	@no_except
	def stars(self):
		try:
			return int(self.match_soup['stars'])
		except:
			return len(self.match_soup.find_all('i', class_='fa fa-star star'))

	@no_except
	def lan(self):
		lan = self.match_soup['lan']
		if lan == 'true':
			return 1
		return 0

	@no_except
	def team_ID(self, num: int):
		'''
		если имеем дело с результатом, то нужно получить ID нужной команды
		'''
		return int(self.match_soup[f"team{num}"])

	@no_except
	def matchTeamName(self):
		try:
			matchTeamName_soup = self.match_soup.find_all('img', class_='team-logo')
			teamName_array = [x['title'] for x in matchTeamName_soup]
			return sorted(set(teamName_array), key=teamName_array.index)
		except:
			matchTeamName_soup = self.match_soup.find_all('div', class_='matchTeamName')
			return [x.text for x in matchTeamName_soup]

	@no_except
	def href(self):
		return self.href_split[-1]

	@no_except
	def matchMeta(self):
		try:
			matchMeta_text = self.match_soup.find('div', class_='matchMeta').text
		except:
			matchMeta_text = self.match_soup.find('div', class_='map-text').text
		if 'bo' in matchMeta_text:
			return matchMeta_text[-1]
		return matchMeta_text

	@no_except
	def matchEventName(self):
		try:
			return self.match_soup.find('div', class_='matchEventName').text
		except:
			# если обе команды не определены
			# получаем название ивента из ссылки
			return self.match_soup.find('span', class_='line-clamp-3').text
		return self.match_soup.find('span', class_='event-name').text
	
	@no_except
	def resultScore(self):
		resultScore_soup = self.match_soup.find('td', class_='result-score').find_all('span')
		return [int(x.text) for x in resultScore_soup]




class Event:
	def __init__(self, event_soup):
		self.event_soup = event_soup
		self.href_split = self.event_soup['href'].split('/')

	def get(self, eventType):
		self.table()

		data = [self.event_ID(), # smallint
				eventType, # varchar(1)
				self.eventName(), # text
				self.location(), # text
				self.dates_array, # interval
				self.prize, # integer
				self.teams # smallint
				]

		return data
	

	def event_ID(self):
		return int(self.href_split[2])

	
	def eventName(self):
		try:
			return self.event_soup.find('div', class_='big-event-name').text
		except:
			return self.event_soup.find('div', class_='text-ellipsis').text

	
	def location(self):
		try:
			return self.event_soup.find('span', class_='big-event-location').text
		except:
			return self.event_soup.find('span', class_='col-desc').text.replace('|','').strip()

	
	def date(self, colDate):
		dates_array = []
		dates_soup = colDate.find_all('span')
		for date_soup in dates_soup:
			try:
				eventTime_Unix = int(date_soup['data-unix'])/1000
			except:
				continue
			dates_array.append(datetime.datetime.utcfromtimestamp(eventTime_Unix))
		return dates_array

	
	@no_except
	def prize(self, table_soup):
		prize_text = table_soup[1].text
		for el in ('$', ','):
			prize_text = prize_text.replace(el, '')
		return int(prize_text)

	
	@no_except
	def teams(self, table_soup):
		return int(table_soup[2].text)
	

	def table(self):
		table_soup = self.event_soup.find('tr').find_all('td')
		
		colDate = table_soup[0]
		try:
			colDate = self.event_soup.find_all('span', class_='col-desc')[-1]
			table_soup = table_soup[::-1]
		except:
			pass

		self.dates_array = self.date(colDate)
		self.prize = self.prize(table_soup)
		self.teams = self.teams(table_soup)
			



class Parse:
	def __init__(self, URL, HEADERS):
		self.DATA = {'matches': [],
					 'events': []
					}
		self.URL = URL
		self.HEADERS = HEADERS
		self.session = requests.Session()
		
	def upcoming_and_live(self):
		response_matches = self.session.get(self.URL + "matches", 
											headers = self.HEADERS)
		soup_matches = BeautifulSoup(response_matches.content, 'html.parser')

		# UPCOMING
		upcomingMatches_soup_array = soup_matches.find_all('div', class_='upcomingMatch')
		self.DATA['matches'].extend([MatchData(upcomingMatch_soup).get('U') for upcomingMatch_soup in upcomingMatches_soup_array])

		# LIVE
		liveMatches_soup_array = soup_matches.find_all('div', class_='liveMatch-container')
		self.DATA['matches'].extend([MatchData(liveMatch_soup).get('L') for liveMatch_soup in liveMatches_soup_array])


	def results(self):
		response_results = self.session.get(self.URL + "results", 
											headers = self.HEADERS)
		soup_results = BeautifulSoup(response_results.content, 'html.parser')

		resultsHolder_allres_soup = soup_results.find('div', class_='results-holder allres')
		result_con_soup_array = resultsHolder_allres_soup.find_all('div', class_='result-con') 

		self.DATA['matches'].extend([MatchData(result_con_soup).get('R') for result_con_soup in result_con_soup_array])

		
	def events(self):
		response_events = self.session.get(self.URL + "events", 
											headers = self.HEADERS)
		soup_events = BeautifulSoup(response_events.content, 'html.parser')

		events_holder_soup = soup_events.find_all('div', class_='events-holder')[-1]

		big_events_soup_array = events_holder_soup.find_all('a', class_='big-event')
		events_soup_array = events_holder_soup.find_all('a', class_='small-event')

		self.DATA['events'].extend([Event(big_event_soup).get('B') for big_event_soup in big_events_soup_array])
		self.DATA['events'].extend([Event(event_soup).get('S') for event_soup in events_soup_array])



p = Parse(URL, HEADERS)
p.upcoming_and_live()

time.sleep(1)

p.results()

time.sleep(1)

p.events()

[print(x) for x in p.DATA['matches']]

[print(x) for x in p.DATA['events']]