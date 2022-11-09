from datetime import datetime

from bot.database import Select
from bot.parse.config import get_flag_smile
from bot.parse.functions import no_except


class EventHandler:
    def __init__(self, event_soup, eventType=None):
        self.event_soup = event_soup
        self.eventType = eventType
        self.href_split = self.event_soup['href'].split('/')

        self.startTime = None
        self.stopTime = None
        self.prize = None
        self.count_teams = None

    def get_info(self):
        self.table()

        data = (self.event_id(),    # smallint
                self.eventType,     # varchar(1)
                self.event_name(),   # text
                self.location(),    # text
                self.flag(),        # varchar(7)
                self.startTime,     # date
                self.stopTime,      # date
                self.prize,         # integer
                self.count_teams    # smallint
                )

        return data

    def event_id(self):
        return int(self.href_split[2])

    def event_name(self):
        try:
            return self.event_soup.find('div', class_='big-event-name').text
        except Exception:
            return self.event_soup.find('div', class_='text-ellipsis').text

    @no_except
    def location(self):
        try:
            return self.event_soup.find('span', class_='big-event-location').text
        except:
            small_country = self.event_soup.find('span', class_='smallCountry')
            return small_country.find('span', class_='col-desc').text.replace(' | ', '')

    @no_except
    def flag(self):
        location = self.event_soup.find('img', class_='flag')['title']
        return get_flag_smile(location)

    def date(self, colDate):
        dates_array = []
        dates_soup = colDate.find_all('span')
        for date_soup in dates_soup:
            try:
                event_time_unix = int(date_soup['data-unix'])/1000
            except Exception:
                continue
            dates_array.append(datetime.utcfromtimestamp(event_time_unix).date())

        if dates_array[0] == dates_array[-1] and self.eventType is None:
            dates_array.append(datetime.utcnow().date())

        return dates_array[0], dates_array[-1]

    @no_except
    def get_prize(self, table_soup):
        prize_text = table_soup[1].text
        for el in ('$', ','):
            prize_text = prize_text.replace(el, '')
        return int(prize_text)

    @no_except
    def get_count_teams(self, table_soup):
        return int(table_soup[2].text)

    def table(self):
        table_soup = self.event_soup.find('tr').find_all('td')

        col_date = table_soup[0]
        try:
            col_date = self.event_soup.find_all('span', class_='col-desc')[-1]
            table_soup = table_soup[::-1]
        except Exception:
            pass

        [self.startTime, self.stopTime] = self.date(col_date)
        self.prize = self.get_prize(table_soup)
        self.count_teams = self.get_count_teams(table_soup)

    # @no_except
    def get_teams_id(self):
        team_logos = self.event_soup.find('div', class_='top-team-logos')
        try:
            teams_id = [Select.team_id_by_exact_name(teamName['title'])[0] for teamName in team_logos.find_all('img')]
            if self.count_teams is None:
                self.count_teams = len(teams_id)
            return teams_id
        except Exception:
            self.count_teams = 0
            return []
