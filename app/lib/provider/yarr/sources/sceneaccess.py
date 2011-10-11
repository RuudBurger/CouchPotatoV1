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
    regex = '<td class="ttr_name">.+?<b>(?P<title>.*?)</b>.+?href="(?P<url>.*?)".*?</td>' 

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

	    new.type = torrent
	    new.url = torrent.group('url')
	    new.name = self.toSaveString(torrent.group('title')
            results.append(new)
	    print new.name + '-' + new.url

        try:
            tables = SoupStrainer('table')
            html = BeautifulSoup(data, parseOnlyThese = tables)
            resultTable = html.find('table', attrs = {'id':'torrents-table'})
            # print resultTable.findAll('tr', attrs = {'class':'tt_row'})
            for result in resultTable.findAll('tr', attrs = {'class':'tt_row'}):
                namecell = result.find('td', attrs = {'class':'ttr_name'})
                datecell = result.find('td', attrs = {'class':'ttr_added'})
                sizecell = result.find('td', attrs = {'class':'ttr_size'})
                seederscell = result.find('td', attrs = {'class':'ttr_seeders'})
                leecherscell = result.find('td', attrs = {'class':'ttr_leechers'})
                linkcell = result.find('td', attrs = {'class':'td_dl'})
                href = namecell.find('a')
                hrefnew = href['href']
                id = hrefnew.replace('details?id=', '')
                id = id.replace('&amp\;hit=1', '')
                id = id.replace('&hit=1', '')
                name = href['title']
                href = linkcell.find('a')
                url = href['href']
                url = 'http://www.sceneaccess.org/' + url
                datec = re.sub('<td class="ttr_added">', '', str(datecell))
                datec = re.sub('<br />(.*)', '', datec)
                size = re.sub('<td class="ttr_size">', '', str(sizecell))
                size = re.sub('<br />(.*)', '', size)
                log.info(id + " - " + name + " - " + url + " - " + datec + " - " + size)
                name = self.toSaveString(name)
                # to item
                new = self.feedItem()
                new.id = id
                new.type = 'special_torrent'
                new.name = name
                new.date = datec
                new.size = self.parseSize(size)
                new.seeders = 100
                new.leechers = 1
                new.url = url
                new.score = self.calcScore(new, movie)
                if Qualities.types.get(type).get('minSize') <= new.size:
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
