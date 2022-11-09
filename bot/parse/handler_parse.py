from datetime import datetime
from bs4 import BeautifulSoup
import requests

from bot.database import Insert

from bot.parse.event import EventHandler
from bot.parse.match import MatchHandler
from bot.parse.news import NewsHandler
from bot.parse.stats_teams import StatsTeamsHandler
from bot.parse.stats_players import StatsPlayersHandler

from bot.parse.functions import time_of_function
from bot.parse.config import main_url, part_links, headers_hltv


class HandlerParse:

    def __init__(self, session=None):
        self.DATA = {'matches': [],
                     'events': [],
                     'teams': [],
                     'news': [],
                     'stats_teams': [],
                     'stats_players': []
                     }
        self.session = session
        if session is None:
            self.session = requests.Session()

    @time_of_function
    def get_soup(self, type_link: str):
        """"""
        if type_link == 'news':
            now = datetime.utcnow()
            year = datetime.strftime(now, '%Y')
            month = datetime.strftime(now, '%B')
            local_path = part_links[type_link](year, month)
        else:
            local_path = part_links[type_link]
        url = main_url + local_path
        response = self.session.get(url, headers=headers_hltv)
        soup = BeautifulSoup(response.content, 'lxml')
        return soup

    def upcoming_and_live(self):
        """"""
        soup_matches = self.get_soup('matches')

        # UPCOMING
        upcoming_matches_soup_array = soup_matches.find_all('div', class_='upcomingMatch')
        for upcoming_match_soup in upcoming_matches_soup_array:
            upcoming_match_info = MatchHandler(upcoming_match_soup, 'U').get_info()
            self.DATA['matches'].append(upcoming_match_info)

        # LIVE
        live_matches_soup_array = soup_matches.find_all('div', class_='liveMatch-container')
        for live_match_soup in live_matches_soup_array:
            live_match_info = MatchHandler(live_match_soup, 'L').get_info()
            self.DATA['matches'].append(live_match_info)

        self.insert('matches')

    def results(self):
        """"""
        soup_results = self.get_soup('results')
        results_holder_allres_soup = soup_results.find('div', class_='results-holder allres')
        result_con_soup_array = results_holder_allres_soup.find_all('div', class_='result-con')

        for result_con_soup in result_con_soup_array:
            result_con_info = MatchHandler(result_con_soup, 'R').get_info()
            self.DATA['matches'].append(result_con_info)

        self.insert('matches')

    def events(self):
        """"""
        def get_soup_array(soup_obj, tag: str, class_: str):
            return soup_obj.find_all(tag, class_=class_)

        soup_events = self.get_soup('events')

        ongoing_events_soup = soup_events.find_all('div', class_='ongoing-events-holder')[-1]
        events_holder_soup = soup_events.find_all('div', class_='events-holder')[-1]

        ongoing_events_soup_array = get_soup_array(ongoing_events_soup, 'a', 'ongoing-event')

        for ongoing_event_soup in ongoing_events_soup_array:
            """"""
            ongoing_event_info = EventHandler(ongoing_event_soup).get_info()
            self.DATA['events'].append(ongoing_event_info)

        for event_type, class_for_find in {'B': 'big-event', 'S': 'small-event'}.items():
            """"""
            events_holder_soup_array = get_soup_array(events_holder_soup, 'a', class_for_find)

            for events_holder_soup in events_holder_soup_array:
                events_holder_info = EventHandler(events_holder_soup, eventType=event_type).get_info()
                self.DATA['events'].append(events_holder_info)

        self.insert('events')

    def news(self):
        """"""
        news_soup = self.get_soup('news')
        all_news_soup_array = news_soup.find_all('a', class_='newsline article')
        for one_news_soup in all_news_soup_array:
            one_news_info = NewsHandler(one_news_soup).get_info()
            self.DATA['news'].append(one_news_info)

        self.insert('news')

    def stats_teams(self):
        """"""
        stats_teams_soup = self.get_soup('stats_teams')
        rating_table = stats_teams_soup.find('table', class_='player-ratings-table').find('tbody')

        for one_team_soup in rating_table.find_all('tr'):
            one_team_info = StatsTeamsHandler(one_team_soup).get_info()
            self.DATA['stats_teams'].append(one_team_info)

        self.insert('stats_teams')

    def stats_players(self):
        stats_players_soup = self.get_soup('stats_players')
        rating_table = stats_players_soup.find('table', class_='player-ratings-table').find('tbody')

        for one_player_soup in rating_table.find_all('tr'):
            one_player_info = StatsPlayersHandler(one_player_soup).get_info()
            self.DATA['stats_players'].append(one_player_info)

        self.insert('stats_players')

    def insert(self, type_: str):
        if type_ == 'events':
            Insert.events(self.DATA['events'])

        elif type_ == 'matches':
            Insert.matches(self.DATA['matches'])

        elif type_ == 'news':
            Insert.news(self.DATA['news'])

        elif type_ == 'stats_teams':
            Insert.stats_teams(self.DATA['stats_teams'])

        elif type_ == 'stats_players':
            Insert.stats_players(self.DATA['stats_players'])

        self.DATA[type_].clear()
