from datetime import datetime

from bot.functions import no_except
from bot.database import Select
from bot.database import Insert


class MatchHandler:
    def __init__(self, match_soup, matchType: str):
        self.match_soup = match_soup
        self.match_type = matchType
        self.href_split = self.match_soup.find('a')['href'].split('/')
        self.team1_name = None
        self.team2_name = None

    def get_info(self):
        self.team_names()

        data = (self.scorebot_id(),                 # integer
                self.match_type,                     # char(1)
                self.match_time_unix(),              # timestamp without time zone
                self.stars(),                       # smallint
                self.lan(),                         # boolean
                self.team_id(1, self.team1_name),   # smallint
                self.team_id(2, self.team2_name),   # smallint
                self.match_meta(),                   # varchar(5)
                self.get_event_id(),                # smallint
                self.result_score()                  # integer[]
                )
        # print(data)
        return data

    @no_except
    def get_event_id(self):
        event_name = self.match_event_name().strip()
        event_id = Select.event_id_by_name(event_name)
        return event_id

    def scorebot_id(self):
        return int(self.href_split[2])

    @no_except
    def match_time_unix(self):
        match_time_unix_str = self.match_soup['data-zonedgrouping-entry-unix']
        match_time_unix_int = int(match_time_unix_str)/1000
        return datetime.utcfromtimestamp(match_time_unix_int)

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
    def team_id(self, num: int, team_name: str):
        try:
            team_id = int(self.match_soup[f"team{num}"])
            Insert.teams([(team_id, team_name)])
        except:
            team_id = Select.team_id_by_exact_name(team_name)[0]
        return team_id

    @no_except
    def team_names(self):
        match_team_name_soup = self.match_soup.find_all('img', class_='matchTeamLogo')
        if not match_team_name_soup:
            match_team_name_soup = self.match_soup.find_all('img', class_='team-logo')

        team_names_array = tuple(match_team_name_soup[x]['title'] for x in (0, -1))

        self.team1_name, self.team2_name = team_names_array[0], team_names_array[-1]
        if self.team1_name == self.team2_name:
            self.team2_name = None

    @no_except
    def href(self):
        return self.href_split[-1]

    @no_except
    def match_meta(self):
        if self.match_type == 'L':
            return self.match_soup['data-maps'].replace(',', ', ')
        try:
            match_meta_text = self.match_soup.find('div', class_='matchMeta').text
        except:
            match_meta_text = self.match_soup.find('div', class_='map-text').text
        if 'bo' in match_meta_text:
            return match_meta_text[-1]
        return match_meta_text

    @no_except
    def match_event_name(self):
        try:
            return self.match_soup.find('div', class_='matchEventName').text
        except:
            # upcoming

            # если обе команды не определены
            # получаем название ивента из ссылки
            # или из строки, но встречаются некорректные названия

            line_clamp_3 = self.match_soup.find('span', class_='line-clamp-3')
            if line_clamp_3 is None:    # if results
                return self.match_soup.find('span', class_='event-name').text

            line_clamp_3_text = line_clamp_3.text
            elements_split = ('-', 'Stage', 'Quarter', 'Semi', 'Grand')
            for x in elements_split:
                line_clamp_3_text = line_clamp_3_text.split(x)[0]

            return line_clamp_3_text

    @no_except
    def result_score(self):
        if self.match_type == 'R':
            result_score_soup = self.match_soup.find('td', class_='result-score').find_all('span')

        # elif self.matchType == 'L':
        # resultScore_soup = self.match_soup.find_all('span', class_='currentMapScore')

        else:
            return
        return [int(x.text) for x in result_score_soup]
