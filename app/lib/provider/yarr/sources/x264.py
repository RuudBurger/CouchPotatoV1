from app.config.cplog import CPLog
from app.lib.provider.yarr.base import torrentBase
from imdb.parser.http.bsouplxml._bsoup import SoupStrainer, BeautifulSoup
from urllib import quote_plus
import time
import urllib
import urllib2

log = CPLog(__name__)

class x264(torrentBase):
    """Provider for #alt.binaries.hdtv.x264 @ EFnet"""

    name = 'x264'
    searchUrl = 'http://85.214.105.230/x264/requests.php?release=%s&status=FILLED&age=1300&sort=ID'
    downloadUrl = 'http://85.214.105.230/get_nzb.php?id=%s&section=hd'

    def __init__(self, config):
        log.info('Using #alt.binaries.hdtv.x264@EFnet provider')

        self.config = config

    def conf(self, option):
        return self.config.get('x264', option)

    def enabled(self):
        return self.conf('enabled') and self.config.get('NZB', 'enabled')

    def find(self, movie, quality, type):

        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results

        url = self.searchUrl % quote_plus(self.toSearchString(movie.name + ' ' + quality))
        log.info('Searching: %s' % url)

        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
        except (IOError, URLError):
            log.error('Failed to open %s.' % url )
            return results

        try:
            tables = SoupStrainer('table')
            html = BeautifulSoup(data, parseOnlyThese = tables)
            resultTable = html.find('table', attrs = {'class':'requests'})
            for result in resultTable.findAll('tr', attrs = {'class':'req_filled'}):
                new = self.feedItem()

                id = result.find('td', attrs = {'class':'reqid'})
                new.id = id.contents[0]
                name = result.find('td', attrs = {'class':'release'})
                new.name = self.toSaveString(name.contents[0])
                new.size = 9999
                new.content = 'x264'
                new.type = 'nzb'
                new.url = self.downloadUrl % (new.id)
                new.date = time.time()
                new.score = self.calcScore(new, movie)

                if self.isCorrectMovie(new, movie, type):
                    results.append(new)
                    log.info('Found: %s' % new.name)
            return results

        except AttributeError:
            log.debug('No search results found.')
        
        return results

    def makeIgnoreString(self, type):
        return ''

    def getInfo(self, url):
        log.debug('Getting info: %s' % url)
        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
            pass
        except IOError:
            log.error('Failed to open %s.' % url)
            return ''

        tables = SoupStrainer('table')
        html = BeautifulSoup(data)
        movieInformation = html.find('div', attrs = {'class':'i_info'})
        return str(movieInformation).decode("utf-8", "replace")
