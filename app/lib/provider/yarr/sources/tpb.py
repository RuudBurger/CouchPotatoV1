from app.config.cplog import CPLog
from app.lib.provider.yarr.base import torrentBase
from app.lib.qualities import Qualities
from dateutil.parser import parse
from imdb.parser.http.bsouplxml._bsoup import SoupStrainer, BeautifulSoup
from urllib import quote_plus
from urllib2 import URLError
import os
import re
import time
import urllib2

log = CPLog(__name__)

class tpb(torrentBase):
    """Api for the Pirate Bay"""

    name = 'The Pirate Bay'
    downloadUrl = 'http://torrents.depiraatbaai.be/%s/%s.torrent'
    nfoUrl = 'https://depiraatbaai.be/torrent/%s'
    detailUrl = 'https://depiraatbaai.be/torrent/%s'
    apiUrl = 'https://depiraatbaai.be/search/%s/0/7/%d'

    catIds = {
        207: ['720p', '1080p'],
        200: ['cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip'],
        202: ['dvdr']
    }
    catBackupId = 200
    ignoreString = {
        '720p': ' -brrip -bdrip',
        '1080p': ' -brrip -bdrip'
    }

    def __init__(self, config):
        log.info('Using TPB.org provider')

        self.config = config

    def conf(self, option):
        return self.config.get('Torrents', option)

    def enabled(self):
        return self.conf('enabled') and (not self.conf('sendto') == 'Blackhole' or (self.conf('blackhole') and os.path.isdir(self.conf('blackhole'))))

    def find(self, movie, quality, type):

        results = []
        if not self.enabled() or not self.isAvailable(self.apiUrl):
            return results

        url = self.apiUrl % (quote_plus(self.toSearchString(movie.name + ' ' + quality) + self.makeIgnoreString(type)), self.getCatId(type))

        log.info('Searching: %s' % url)

        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return results

        try:
            tables = SoupStrainer('table')
            html = BeautifulSoup(data, parseOnlyThese = tables)
            resultTable = html.find('table', attrs = {'id':'searchResult'})
            for result in resultTable.findAll('tr'):
                details = result.find('a', attrs = {'class':'detLink'})
                if details:
                    href = re.search('/(?P<id>\d+)/', details['href'])
                    id = href.group('id')
                    name = self.toSaveString(details.contents[0])
                    desc = result.find('font', attrs = {'class':'detDesc'}).contents[0].split(',')
                    date = ''
                    size = 0
                    for item in desc:
                        # Weird date stuff
                        if 'uploaded' in item.lower():
                            date = item.replace('Uploaded', '')
                            date = date.replace('Today', '')

                            # Do something with yesterday
                            yesterdayMinus = 0
                            if 'Y-day' in date:
                                date = date.replace('Y-day', '')
                                yesterdayMinus = 86400

                            datestring = date.replace('&nbsp;', ' ').strip()
                            date = int(time.mktime(parse(datestring).timetuple())) - yesterdayMinus
                        # size
                        elif 'size' in item.lower():
                            size = item.replace('Size', '')

                    seedleech = []
                    for td in result.findAll('td'):
                        try:
                            seedleech.append(int(td.contents[0]))
                        except ValueError:
                            pass

                    seeders = 0
                    leechers = 0
                    if len(seedleech) == 2 and seedleech[0] > 0 and seedleech[1] > 0:
                        seeders = seedleech[0]
                        leechers = seedleech[1]

                    # to item
                    new = self.feedItem()
                    new.id = id
                    new.type = 'torrent'
                    new.name = name
                    new.date = date
                    new.size = self.parseSize(size)
                    new.seeders = seeders
                    new.leechers = leechers
                    new.url = self.downloadLink(id, name)
                    new.score = self.calcScore(new, movie) + self.uploader(result) + (seeders / 10)

                    if seeders > 0 and (new.date + (int(self.conf('wait')) * 60 * 60) < time.time()) and Qualities.types.get(type).get('minSize') <= new.size:
                        new.detailUrl = self.detailLink(id)
                        new.content = self.getInfo(new.detailUrl)
                        if self.isCorrectMovie(new, movie, type):
                            results.append(new)
                            log.info('Found: %s' % new.name)

            return results

        except AttributeError:
            log.debug('No search results found.')

        return []

    def makeIgnoreString(self, type):
        ignore = self.ignoreString.get(type)
        return ignore if ignore else ''

    def uploader(self, html):
        score = 0
        if html.find('img', attr = {'alt':'VIP'}):
            score += 3
        if html.find('img', attr = {'alt':'Trusted'}):
            score += 1
        return score


    def getInfo(self, url):
        log.debug('Getting info: %s' % url)
        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
            pass
        except IOError:
            log.error('Failed to open %s.' % url)
            return ''

        div = SoupStrainer('div')
        html = BeautifulSoup(data, parseOnlyThese = div)
        html = html.find('div', attrs = {'class':'nfo'})
        return str(html).decode("utf-8", "replace")

    def downloadLink(self, id, name):
        return self.downloadUrl % (id, quote_plus(name))
