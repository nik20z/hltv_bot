import datetime
import lxml
import requests
import time

from pprint import pprint
from bs4 import BeautifulSoup

from .config import MAIN_URL, PART_LINKS, HEADERS
from telegram.config import FLAG_SMILE
from functions import no_except, time_of_function




class Match:
	def __init__(self, INSERT, SELECT, match_soup, matchType: str):
		self.INSERT = INSERT
		self.SELECT = SELECT
		self.match_soup = match_soup
		self.matchType = matchType
		self.href_split = self.match_soup.find('a')['href'].split('/')
		self.team1_name = None
		self.team2_name = None

	def get_info(self):
		self.teamNames()
		
		data = (self.scorebot_ID(), # integer
				self.matchType, # char(1)
				self.matchTime_Unix(), # timestamp without time zone 
				self.stars(), # smallint
				self.lan(), # boolean
				self.team_ID(1, self.team1_name), # smallint
				self.team_ID(2, self.team2_name), # smallint
				self.matchMeta(), # varchar(5)
				self.get_event_ID(), # smallint
				self.resultScore() # integer[]
				)
		print(data)
		return data

	@no_except
	def get_event_ID(self):
		event_name = self.matchEventName().strip()
		event_id = self.SELECT.event_id_by_name(event_name)
		return event_id

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
		return self.match_soup['lan'] == 'true'

	@no_except
	def team_ID(self, num: int, team_name: str):
		return self.SELECT.team_id_by_name(team_name, one_result=True)[0]
		'''
		team_id = self.SELECT.team_id_by_name(team_name, one_result=True)
		if team_id is None:
			team_id = int(self.match_soup[f"team{num}"])
			self.INSERT.teams([(team_id, team_name)])
			return team_id
		return team_id[0]
		'''

	@no_except
	def teamNames(self):
		matchTeamName_soup = self.match_soup.find_all('img', class_='matchTeamLogo')
		if matchTeamName_soup == []:
			matchTeamName_soup = self.match_soup.find_all('img', class_='team-logo')

		teamNames_array = tuple(matchTeamName_soup[x]['title'] for x in (0,-1))

		self.team1_name, self.team2_name = teamNames_array[0], teamNames_array[-1]
		if self.team1_name == self.team2_name:
			self.team2_name = None

	@no_except
	def href(self):
		return self.href_split[-1]

	@no_except
	def matchMeta(self):
		if self.matchType == 'L':
			return self.match_soup['data-maps'].replace(',', ', ')
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
		except: # upcoming
			# если обе команды не определены
			# получаем название ивента из ссылки
			# или из строки, но встречаются некорректные названия
			line_clamp_3 = self.match_soup.find('span', class_='line-clamp-3')
			if line_clamp_3 == None:
				return self.match_soup.find('span', class_='event-name').text

			line_clamp_3_text = line_clamp_3.text
			elements_split = ('-', 'Stage', 'Quarter', 'Semi', 'Grand') 
			for x in elements_split:
				line_clamp_3_text = line_clamp_3_text.split(x)[0]

			return line_clamp_3_text
	
	@no_except
	def resultScore(self):
		if self.matchType == 'R':
			resultScore_soup = self.match_soup.find('td', class_='result-score').find_all('span')
		#elif self.matchType == 'L':
			#resultScore_soup = self.match_soup.find_all('span', class_='currentMapScore')
		else:
			return 
		return [int(x.text) for x in resultScore_soup]




class Event:
	def __init__(self, SELECT, event_soup, eventType = None):
		self.SELECT = SELECT
		self.event_soup = event_soup
		self.eventType = eventType
		self.href_split = self.event_soup['href'].split('/')

	def get_info(self):
		self.table()
		
		data = (self.event_ID(), # smallint
				self.eventType, # varchar(1)
				self.eventName(), # text
				self.location(), # text
				self.flag(), # varchar(7)
				self.startTime, # date
				self.stopTime, # date
				self.prize, # integer
				self.count_teams # smallint
				)

		return data
	

	def event_ID(self):
		return int(self.href_split[2])
	
	def eventName(self):
		try:
			return self.event_soup.find('div', class_='big-event-name').text
		except:
			return self.event_soup.find('div', class_='text-ellipsis').text

	@no_except
	def location(self):
		try:
			return self.event_soup.find('span', class_='big-event-location').text
		except:
			return self.event_soup.find('span', class_='smallCountry').find('span', class_='col-desc').text.replace(' | ', '')

	@no_except
	def flag(self):
		location = self.event_soup.find('img', class_='flag')['title']
		return FLAG_SMILE(location)
	

	def date(self, colDate):
		dates_array = []
		dates_soup = colDate.find_all('span')
		for date_soup in dates_soup:
			try:
				eventTime_Unix = int(date_soup['data-unix'])/1000
			except:
				continue
			dates_array.append(datetime.datetime.utcfromtimestamp(eventTime_Unix).date())
		
		if dates_array[0] == dates_array[-1] and self.eventType is None:
			dates_array.append(datetime.datetime.utcnow().date())
		
		return dates_array[0], dates_array[-1]

	@no_except
	def prize(self, table_soup):
		prize_text = table_soup[1].text
		for el in ('$', ','):
			prize_text = prize_text.replace(el, '')
		return int(prize_text)
	
	@no_except
	def count_teams(self, table_soup):
		return int(table_soup[2].text)

	def table(self):
		table_soup = self.event_soup.find('tr').find_all('td')
		
		colDate = table_soup[0]
		try:
			colDate = self.event_soup.find_all('span', class_='col-desc')[-1]
			table_soup = table_soup[::-1]
		except:
			pass

		[self.startTime, self.stopTime] = self.date(colDate)
		self.prize = self.prize(table_soup)
		self.count_teams = self.count_teams(table_soup)

	#@no_except
	def get_teams_id(self):
		team_logos = self.event_soup.find('div', class_='top-team-logos')
		try:
			teams_id = [self.SELECT.team_id_by_name(teamName['title'])[0] for teamName in team_logos.find_all('img')]
			if self.count_teams is None:
				self.count_teams = len(teams_id)
			return teams_id
		except:
			self.count_teams = 0
			return []
		
				



class News:

	def __init__(self, news_soup):
		self.news_soup = news_soup
		self.href_split = self.news_soup['href'].split('/')
		

	def get_info(self):
		news_id = int(self.href_split[-2])
		date_text = self.news_soup.find('div', class_='newsrecent').text
		date_ = datetime.datetime.strptime(date_text, '%Y-%m-%d').date()
		location = self.news_soup.find('img')['title']
		country_flag = FLAG_SMILE(location)
		newstext = self.news_soup.find('div', class_='newstext').text
		href = self.href_split[-1]
		
		data = (news_id, 
				date_,
				newstext,
				country_flag,
				href
				)
		return data



class StatsTeams:

	def __init__(self, team_soup):
		self.team_soup = team_soup
		self.href_split = self.team_soup.find('a')['href'].split('/')

	def get_info(self):
		data = (int(self.team_id()),
				self.team_name(),
				self.flag(),
				int(self.maps()),
				int(self.kdDiff()),
				float(self.KD()),
				float(self.rating()),
			)
		return data

	def value(self, tag: str, class_: str):
		return self.team_soup.find(tag, class_=class_).text

	def team_id(self):
		return self.href_split[-2]

	def team_name(self):
		return self.team_soup.find('a').text

	def flag(self):
		country = self.team_soup.find('img')['title']
		return FLAG_SMILE(country)

	def maps(self):
		return self.value('td', 'statsDetail')

	def kdDiff(self):
		return self.value('td', 'kdDiffCol')

	def KD(self):
		return self.team_soup.find_all('td', class_='statsDetail')[-1].text

	def rating(self):
		return self.value('td', 'ratingCol')



class StatsPlayers:

	def __init__(self, player_soup):
		self.smiles_tuple = []

		self.player_soup = player_soup
		self.href_split = self.player_soup.find('a')['href'].split('/')

	def get_info(self):

		data = (int(self.player_id()),
				self.player_nik_name(),
				self.flag(),
				int(self.number_maps()),
				int(self.number_rounds()),
				int(self.kdDiff()),
				float(self.KD()),
				float(self.rating())
			)
		return data

	def value(self, tag: str, class_: str):
		return self.player_soup.find(tag, class_=class_).text

	def player_id(self):
		return self.href_split[-2]

	def player_nik_name(self):
		return self.player_soup.find('a').text

	def flag(self):
		country = self.player_soup.find('img')['title']
		return FLAG_SMILE(country)

	def number_maps(self):
		return self.value('td', 'statsDetail')

	def number_rounds(self):
		return self.value('td', 'statsDetail gtSmartphone-only')

	def kdDiff(self):
		return self.value('td', 'kdDiffCol')

	def KD(self):
		return self.player_soup.find_all('td', class_='statsDetail')[-1].text

	def rating(self):
		return self.value('td', 'ratingCol')




class Parse:

	def __init__(self, INSERT, SELECT, UPDATE, session):
		self.DATA = {'matches': [],
					 'events': [],
					 'teams': [],
					 'news': [],
					 'stats_teams': [],
					 'stats_players': []
					}
		self.INSERT = INSERT
		self.SELECT = SELECT
		self.UPDATE = UPDATE
		self.session = session


	@time_of_function
	def get_soup(self, type_link: str):
		if type_link == 'news':
			now = datetime.datetime.utcnow()
			year = datetime.datetime.strftime(now, '%Y')
			month = datetime.datetime.strftime(now, '%B')
			local_path = PART_LINKS[type_link](year, month)
		else:
			local_path = PART_LINKS[type_link]
		url = MAIN_URL + local_path
		response = self.session.get(url, headers=HEADERS)
		soup = BeautifulSoup(response.content, 'lxml')
		return soup
	
	
	def upcoming_and_live(self):
		soup_matches = self.get_soup('matches')

		# UPCOMING
		upcomingMatches_soup_array = soup_matches.find_all('div', class_='upcomingMatch')
		self.DATA['matches'].extend([Match(self.INSERT, self.SELECT, upcomingMatch_soup, 'U').get_info() for upcomingMatch_soup in upcomingMatches_soup_array])

		# LIVE
		liveMatches_soup_array = soup_matches.find_all('div', class_='liveMatch-container')
		self.DATA['matches'].extend([Match(self.INSERT, self.SELECT, liveMatch_soup, 'L').get_info() for liveMatch_soup in liveMatches_soup_array])

	
	def results(self):	
		soup_results = self.get_soup('results')
		resultsHolder_allres_soup = soup_results.find('div', class_='results-holder allres')
		result_con_soup_array = resultsHolder_allres_soup.find_all('div', class_='result-con') 

		self.DATA['matches'].extend([Match(self.INSERT, self.SELECT, result_con_soup, 'R').get_info() for result_con_soup in result_con_soup_array])


	def teams(self):
		pass

	
	def events(self):
		def get_soup_array(soup_obj, tag: str, class_: str):
			return soup_obj.find_all(tag, class_=class_)

		soup_events = self.get_soup('events')

		ongoing_events_soup = soup_events.find_all('div', class_='ongoing-events-holder')[-1]
		events_holder_soup = soup_events.find_all('div', class_='events-holder')[-1]

		ongoing_events_soup_array = get_soup_array(ongoing_events_soup, 'a', 'ongoing-event')
		
		self.DATA['events'].extend([Event(self.SELECT, ongoing_event_soup).get_info() for ongoing_event_soup in ongoing_events_soup_array])

		for event_type, class_for_find in {'B': 'big-event', 'S': 'small-event'}.items():
			events_holder_soup_array = get_soup_array(events_holder_soup, 'a', class_for_find)
			events_data_array = [Event(self.SELECT, x_soup, eventType=event_type).get_info() for x_soup in events_holder_soup_array]
			self.DATA['events'].extend(events_data_array)

		self.insert('events')

	
	def news(self):
		news_soup = self.get_soup('news')
		all_news_soup_array = news_soup.find_all('a', class_='newsline article')
		news_data_array = [News(x).get_info() for x in all_news_soup_array]

		self.DATA['news'].extend(news_data_array)

		self.insert('news')


	def stats_teams(self):
		stats_teams_soup = self.get_soup('stats_teams')
		rating_table = stats_teams_soup.find('table', class_='player-ratings-table').find('tbody')

		stats_teams_array = [StatsTeams(x).get_info() for x in rating_table.find_all('tr')]

		self.DATA['stats_teams'].extend(stats_teams_array)

		self.insert('stats_teams')

	def stats_players(self):
		stats_players_soup = self.get_soup('stats_players')
		rating_table = stats_players_soup.find('table', class_='player-ratings-table').find('tbody')

		stats_players_array = [StatsPlayers(x).get_info() for x in rating_table.find_all('tr')]

		self.DATA['stats_players'].extend(stats_players_array)

		self.insert('stats_players')


	def insert(self, type_: str):
		if type_ == 'events':
			self.INSERT.events(self.DATA['events'])
		
		elif type_ == 'matches':
			self.INSERT.matches(self.DATA['matches'])

		elif type_ == 'news':
			self.INSERT.news(self.DATA['news'])

		elif type_ == 'stats_teams':
			self.INSERT.stats_teams(self.DATA['stats_teams'])

		elif type_ == 'stats_players':
			self.INSERT.stats_players(self.DATA['stats_players'])



	
	




#@no_except
def UpdateData(INSERT, SELECT, UPDATE, data_types: list, interval = None):
	
	while True:
				
		session = requests.Session()
		p = Parse(INSERT, SELECT, UPDATE, session)

		if 'events' in data_types:
			p.events()

		if 'matches' in data_types:
			p.upcoming_and_live()
			p.results()
			p.insert('matches')

		if 'news' in data_types:
			p.news()

		if 'stats_teams' in data_types:
			p.stats_teams()

		if 'stats_players' in data_types:
			p.stats_players()

		if interval is None:
			return

		time.sleep(interval)
	