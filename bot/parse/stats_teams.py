from bot.parse.config import get_flag_smile


class StatsTeamsHandler:

    def __init__(self, team_soup):
        self.team_soup = team_soup
        self.href_split = self.team_soup.find('a')['href'].split('/')

    def get_info(self):
        data = (int(self.team_id()),
                self.team_name(),
                self.flag(),
                int(self.maps()),
                int(self.kd_diff()),
                float(self.kd()),
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
        return get_flag_smile(country)

    def maps(self):
        return self.value('td', 'statsDetail')

    def kd_diff(self):
        return self.value('td', 'kdDiffCol')

    def kd(self):
        return self.team_soup.find_all('td', class_='statsDetail')[-1].text

    def rating(self):
        return self.value('td', 'ratingCol')
