from datetime import datetime

from bot.parse.config import get_flag_smile


class NewsHandler:
    def __init__(self, news_soup):
        self.news_soup = news_soup
        self.href_split = self.news_soup['href'].split('/')

    def get_info(self):
        news_id = int(self.href_split[-2])
        date_text = self.news_soup.find('div', class_='newsrecent').text
        date_ = datetime.strptime(date_text, '%Y-%m-%d').date()
        location = self.news_soup.find('img')['title']
        country_flag = get_flag_smile(location)
        newstext = self.news_soup.find('div', class_='newstext').text
        href = self.href_split[-1]

        data = (news_id,
                date_,
                newstext,
                country_flag,
                href
                )
        return data
