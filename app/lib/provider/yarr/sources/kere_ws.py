from app.config.cplog import CPLog
from app.lib.provider.yarr.base import nzbBase
from dateutil.parser import parse
from urllib import urlencode
from urllib2 import URLError
import time
import traceback

log = CPLog(__name__)

class kereWs(nzbBase):
    """Api for Kere.ws"""

    name = 'KereWS'
    downloadUrl = 'http://kere.ws/api?t=get&id=%s%s'
    detailUrl = 'http://kere.ws/api?t=details&id=%s'
    searchUrl = 'http://kere.ws/api'

    catIds = {
        1000: ['720p', '1080p','cam', 'ts', 'dvdrip', 'tc', 'r5', 'scr', 'brrip', 'dvdr'],
    }
    catBackupId = 2

    timeBetween = 10 # Seconds

    def __init__(self, config):
        log.info('Using Kere.ws provider')

        self.config = config

    def conf(self, option):
        return self.config.get('kere_ws', option)

    def enabled(self):
        return self.conf('enabled') and self.config.get('NZB', 'enabled') and self.conf('username') and self.conf('apikey')

    def find(self, movie, quality, type, retry = False):

        self.cleanCache();

        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results

        catId = self.getCatId(type)
        arguments = urlencode({
            't' : 'movie',
            'imdbid': movie.imdb.replace('tt',''),
            'cat': catId,
            'apikey': self.conf('apikey'),
        })
        url = "%s?%s" % (self.searchUrl, arguments)
        cacheId = str(movie.imdb) + '-' + str(catId)
        singleCat = (len(self.catIds.get(catId)) == 1 and catId != self.catBackupId)

        try:
            cached = False
            if self.cache.get(cacheId):
                data = True
                cached = True
                log.info('Getting RSS from cache: %s.' % cacheId)
            else:
                log.info('Searching: %s' % url)
                data = self.urlopen(url)
                self.cache[cacheId] = {
                    'time': time.time()
                }
        except IOError, URLError:
            log.error('Failed to open %s.' % url)
            return results

        if data:
            try:
                try:
                    if cached:
                        xml = self.cache[cacheId]['xml']
                    else:
                        xml = self.getItems(data)
                        self.cache[cacheId]['xml'] = xml
                except:
                    log.debug('No valid xml or to many requests.. You never know with %s.' % self.name)
                    return results

                for nzb in xml:

                    title = self.gettextelement(nzb, "title")
                    if 'error' in title.lower(): continue

                    id = self.gettextelement(nzb, "link").replace('http://kere.ws/getnzb/','').split('.')[0]
                    size = '%f KB' % (float(str(nzb.find('enclosure').attrib).split("'length': ")[1].split(',')[0].strip("'").strip()) / 1024)
                    date = str(self.gettextelement(nzb, "pubDate"))
                    new = self.feedItem()
                    new.id = str(id)
                    new.type = 'nzb'
                    new.name = title
                    #new.date = int(time.mktime(parse(date).timetuple()))
                    new.date = date
                    new.size = self.parseSize(size)
                    new.url = self.downloadLink(id)
                    new.detailUrl = self.detailLink(id)
                    new.content = self.gettextelement(nzb, "description")
                    new.score = self.calcScore(new, movie)
                    new.checkNZB = True

                    if self.isCorrectMovie(new, movie, type, imdbResults = True, singleCategory = singleCat):
                        results.append(new)
                        log.info('Found: %s' % new.name)

                return results
            except:
                log.error('Failed to parse XML response from Kere.ws: %s' % traceback.format_exc())

        return results

    def getApiExt(self):
        return '&username=%s&apikey=%s' % (self.conf('username'), self.conf('apikey'))
