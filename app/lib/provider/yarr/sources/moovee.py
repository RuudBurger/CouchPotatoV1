from app.config.cplog import CPLog
from app.lib.provider.yarr.base import torrentBase
from imdb.parser.http.bsouplxml._bsoup import SoupStrainer, BeautifulSoup
from urllib import quote_plus
import time
import urllib
import urllib2
import re
import cookielib


log = CPLog(__name__)

class moovee(torrentBase):
    """Provider for #alt.binaries.moovee @ EFnet"""

    name = 'moovee'
    searchUrl = 'http://abmoovee.allfilled.com/search.php?q=%s&Search=Search'
    downloadUrl = 'http://85.214.105.230/get_nzb.php?id=%s&section=moovee'
    regex = '<td class="cell_reqid">(?P<reqid>.*?)</td>.+?<td class="cell_request">(?P<title>.*?)</td>'

    def __init__(self, config):
        log.info('Using #alt.binaries.moovee@EFnet provider')

        self.config = config

    def conf(self, option):
        return self.config.get('moovee', option)

    def enabled(self):
        return self.conf('enabled') and self.config.get('NZB', 'enabled')

    def find(self, movie, quality, type):

        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results

        url = self.searchUrl % quote_plus(self.toSearchString(movie.name + ' ' + quality))
        log.info('Searching: %s' % url)

        try:
           cookiejar = cookielib.CookieJar()
           opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
           urllib2.install_opener(opener)
           f = opener.open(url)
           data = f.read()
           f.close()
        
        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return results

        match = re.compile(self.regex, re.DOTALL ).finditer(data)
        for nzb in match:
            new = self.feedItem()
            new.type = 'nzb'
            new.content = 'moovee'
            new.size = 1400
            new.name = self.toSaveString(nzb.group('title'))
            downloadURL = self.downloadUrl % (urllib.quote(nzb.group('reqid')))
            new.url = downloadURL
            new.date = time.time()
            new.score = self.calcScore(new, movie)
            
            if self.isCorrectMovie(new, movie, type):
                results.append(new)
                log.info('Found: %s' % new.name)
        return results
