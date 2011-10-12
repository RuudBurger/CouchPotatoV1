from app.config.cplog import CPLog
from app.lib.provider.yarr.base import torrentBase
from app.lib.qualities import Qualities
from dateutil.parser import parse
from imdb.parser.http.bsouplxml._bsoup import SoupStrainer, BeautifulSoup
from urllib import quote_plus
from urllib2 import URLError
import logging
import os
import re
import time
import urllib
import urllib2
import cookielib

log = CPLog(__name__)

class sceneaccess(torrentBase):
    """Provider for SceneAccess"""

    name = 'SceneAccess'
    downloadUrl = 'http://www.sceneaccess.org/download/%d/%s/%s.torrent'
    nfoUrl = 'http://www.sceneaccess.org/details?id=%s'
    detailUrl = 'http://www.sceneaccess.org/details?id=%s'
    searchUrl = 'http://www.sceneaccess.org/browse?search=%s&method=2&c%d=%d'
    regex = '<td class="ttr_name"><a href="details\?id=(?P<id>.*?)".+?<b>(?P<title>.*?)</b>.+?href="(?P<url>.*?)".*?</td>.+?<td class="ttr_size">(?P<size>.*?)<br />' 

    catIds = {
     22: ['720p', '1080p'],
     7: ['cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip'],
     8: ['dvdr']
    }
	
    catBackupId = 7
    ignoreString = {
        '720p': ' -brrip -bdrip',
        '1080p': ' -brrip -bdrip'
    }

    def __init__(self, config):
        log.info('Using SceneAccess provider')

        self.config = config

    def conf(self, option):
        return self.config.get('sceneaccess', option)

    def conf_torrents(self, option):
        return self.config.get('Torrents', option)

    def enabled(self):
        return self.conf('enabled') and (not self.conf_torrents('sendto') == 'Blackhole' or (self.conf_torrents('blackhole') and os.path.isdir(self.conf_torrents('blackhole'))))

    def find(self, movie, quality, type):

        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results

        url = self.searchUrl % (quote_plus(self.toSearchString(movie.name + ' ' + quality) + self.makeIgnoreString(type)), self.getCatId(type), self.getCatId(type))
        log.info('Searching: %s' % url)

        try:
	    cookiejar = cookielib.CookieJar()
	    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
	    urllib2.install_opener(opener)
	    params = urllib.urlencode(dict(username='' + self.conf('username'), password='' + self.conf('password'), submit='come on in'))
	    f = opener.open('http://www.sceneaccess.org/login', params)
	    data = f.read()
	    f.close()
	    f = opener.open(url)
	    data = f.read()
	    f.close()

        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return results

        match = re.compile(self.regex, re.DOTALL ).finditer(data)

        for torrent in match:
	    new = self.feedItem()
	    new.type = 'torrent'
	    new.url = 'http://www.sceneaccess.org/' + torrent.group('url')
	    new.name = self.toSaveString(torrent.group('title'))
	    new.size = self.parseSize(torrent.group('size'))
	    new.id = torrent.group('id')
	    new.score = self.calcScore(new, movie)
	    if Qualities.types.get(type).get('minSize') <= new.size:
              new.detailUrl = self.detailLink(new.id)
              new.content = self.getInfo(new.detailUrl)
              if self.isCorrectMovie(new, movie, type):
                 results.append(new)
                 log.info('Found: %s' % new.name)
        return results

        return []

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

    def downloadLink(self, id, name):
        return self.downloadUrl % (id, quote_plus(name))
