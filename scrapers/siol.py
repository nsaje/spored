from datetime import time, date, datetime
import urllib2

from bs4 import BeautifulSoup

import base
import config


BASE_URL = 'http://www.siol.net/tv-spored.aspx'
BASE_URL_CHAN = BASE_URL + '?ch=%(ch)s&p1=%(offset)s&p3=0&p4=0'
SIOL_CHANNELS = dict((ch, ch.replace(' ', '+')) for ch in config.CHANNELS)


class SiolScraper(base.Scraper):

    @staticmethod
    def scrape_channel(channel, day):
        day_offset = int((day - date.today()).total_seconds() // (3600*24) + 1)
        if not -1 <= day_offset <= 4:
            raise Exception("Offset too large")

        url = BASE_URL_CHAN % {'ch': SIOL_CHANNELS[channel],
                               'offset': day_offset}
        handle = urllib2.urlopen(url)
        s = BeautifulSoup(handle.read())

        entries = []
        for i, entry_div in enumerate(s.find_all('div', class_='def')):
            spans = entry_div.find_all('span')
            time_split = map(int, spans[0].string.split(':'))
            uuid = spans[1].a['href']
            title = spans[1].string
            timestamp = datetime.combine(day, time(*time_split))
            timestamp_unix = int(timestamp.strftime('%s'))
            entries.append(dict(timestamp=timestamp,
                                from_time=timestamp_unix,
                                channel=channel,
                                uuid=uuid,
                                title=title))
            if i > 0:
                entries[i-1]['to_time'] = timestamp_unix
        entries[-1]['to_time'] = None
        return entries

    @staticmethod
    def scrape_description(uuid):
        url = BASE_URL + uuid
        handle = urllib2.urlopen(url)
        s = BeautifulSoup(handle.read())

        p_genre = s.find_all('p', class_='zanr')[0]
        genre = p_genre.string
        description = '\n'.join(p_genre.next_sibling.stripped_strings)
        return dict(uuid=uuid,
                    genre=genre,
                    description=description)

if __name__ == '__main__':
    print SiolScraper.scrape_channel('TV SLO 1', date.today())
    # print SiolScraper.scrape_description('?p2=OBMCTfddADR5vuAIOiVjGA%3d%3d')
    pass

