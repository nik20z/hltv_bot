from bot.parse.config import get_flag_smile


class StatsPlayersHandler:
    def __init__(self, player_soup):
        self.player_soup = player_soup
        self.href_player_split = self.player_soup.find('a')['href'].split('/')

    def get_info(self):
        data = (int(self.player_id()),
                self.team_id(),
                self.player_nik_name(),
                self.flag(),
                int(self.number_maps()),
                int(self.number_rounds()),
                int(self.kd_diff()),
                float(self.kd()),
                float(self.rating())
                )

        return data

    def value(self, tag: str, class_: str):
        return self.player_soup.find(tag, class_=class_).text

    def player_id(self):
        return self.href_player_split[-2]

    def team_id(self):
        href_team_split = self.player_soup.find('td', class_='teamCol').find('a')['href']
        return href_team_split.split('/')[-2]

    def player_nik_name(self):
        return self.player_soup.find('a').text

    def flag(self):
        country = self.player_soup.find('img')['title']
        return get_flag_smile(country)

    def number_maps(self):
        return self.value('td', 'statsDetail')

    def number_rounds(self):
        return self.value('td', 'statsDetail gtSmartphone-only')

    def kd_diff(self):
        return self.value('td', 'kdDiffCol')

    def kd(self):
        return self.player_soup.find_all('td', class_='statsDetail')[-1].text

    def rating(self):
        return self.value('td', 'ratingCol')
