from app.config.cplog import CPLog
from app.lib.provider.yarr.base import torrentBase
from imdb.parser.http.bsouplxml._bsoup import SoupStrainer, BeautifulSoup
from urllib import quote_plus
import time
import urllib
import urllib2
import re 

log = CPLog(__name__)

class mysterbin(torrentBase):
    """Provider for MysterBin"""

    name = 'mysterbin'
    searchUrl = 'http://www.mysterbin.com/search?q=%s&fytype=1&fsize=6'
    downloadUrl = 'http://www.mysterbin.com/nzb?c=%s'

    def __init__(self, config):
        log.info('Using Mystery Bin')

        self.config = config

    def conf(self, option):
        return self.config.get('mysterbin', option)

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
            resultable = html.find('table', attrs = {'class':'t'})
            for result in resultable.findAll('span', attrs = {'class':'cname'}):
                new = self.feedItem()
                a = result.find('a')
                id  = re.search('(?<=detail\?c\=)\w+', a['href'])
                new.id = id.group(0)
                text = a.findAll(text=True)
                words = ''
                for text in a.findAll(text=True):
                    words = words + unicode(text).encode('utf-8')
                new.name = words
                new.size = 9999
                new.content = 'mysterbin'
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
        
        return ''
 


