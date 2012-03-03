from app.config.cplog import CPLog
from app.lib.provider.yarr.base import nzbBase
from dateutil.parser import parse
from urllib import urlencode
from urllib2 import URLError
import time
import traceback
import urllib
import urllib2

log = CPLog(__name__)

class newzbin(nzbBase):
    """Api for newzbin"""

    name = 'Newzbin'
    searchUrl = 'https://www.newzbin2.es/search/'
    downloadUrl = 'http://www.newzbin2.es/api/dnzb/'
    REPORT_NS_OLD = 'http://www.newzbin.com/DTD/2007/feeds/report/'
    REPORT_NS = 'http://www.newzbin2.es/DTD/2007/feeds/report/'

    formatIds = {
        2: ['scr'],
        1: ['cam'],
        4: ['tc'],
        8: ['ts'],
        1024: ['r5'],
    }
    catIds = {
        2097152: ['1080p'],
        524288: ['720p'],
        262144: ['brrip'],
        2: ['dvdr'],
    }
    catBackupId = -1

    timeBetween = 10 # Seconds

    def __init__(self, config):
        log.info('Using newzbin provider')
        self.config = config

    def conf(self, option):
        return self.config.get('newzbin', option)

    def enabled(self):
        return self.conf('enabled') and self.config.get('NZB', 'enabled') and self.conf('username') and self.conf('password')

    def find(self, movie, quality, type, retry = False):

        self.cleanCache();

        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results

        formatId = self.getFormatId(type)
        catId = self.getCatId(type)

        arguments = urlencode({
            'searchaction': 'Search',
            'u_url_posts_only': '0',
            'u_show_passworded': '0',
            'q_url': 'imdb.com/title/' + movie.imdb,
            'sort': 'ps_totalsize',
            'order': 'asc',
            'u_post_results_amt': '100',
            'feed': 'rss',
            'category': '6',
            'ps_rb_video_format': str(catId),
            'ps_rb_source': str(formatId),
        })

        url = "%s?%s" % (self.searchUrl, arguments)
        cacheId = str('%s %s %s' % (movie.imdb, str(formatId), str(catId)))
        singleCat = True

        try:
            cached = False
            if(self.cache.get(cacheId)):
                data = True
                cached = True
                log.info('Getting RSS from cache: %s.' % cacheId)
            else:
                log.info('Searching: %s' % url)
                data = self.urlopen(url, username = self.conf('username'), password = self.conf('password'))
                self.cache[cacheId] = {
                    'time': time.time()
                }

        except (IOError, URLError):
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

                for item in xml:

                    title = self.gettextelement(item, "title")
                    if 'error' in title.lower(): continue

                    try:
                      for attr in item.find('{%s}attributes' % self.REPORT_NS):
                        title += ' ' + attr.text
                        REPORT_NS = self.REPORT_NS
                    except:
                      for attr in item.find('{%s}attributes' % self.REPORT_NS_OLD):
                        title += ' ' + attr.text
                        REPORT_NS = self.REPORT_NS_OLD
                    
                    id = int(self.gettextelement(item, '{%s}id' % REPORT_NS))
                    size = str(int(self.gettextelement(item, '{%s}size' % REPORT_NS)) / 1024 / 1024) + ' mb'
                    date = str(self.gettextelement(item, '{%s}postdate' % REPORT_NS))

                    new = self.feedItem()
                    new.id = id
                    new.type = 'nzb'
                    new.name = title
                    new.date = int(time.mktime(parse(date).timetuple()))
                    new.size = self.parseSize(size)
                    new.url = str(self.gettextelement(item, '{%s}nzb' % REPORT_NS))
                    new.detailUrl = str(self.gettextelement(item, 'link'))
                    new.content = self.gettextelement(item, "description")
                    new.score = self.calcScore(new, movie)
                    new.addbyid = True
                    new.checkNZB = False
                    new.download = self.download

                    if self.isCorrectMovie(new, movie, type, imdbResults = True, singleCategory = singleCat):
                        results.append(new)
                        log.info('Found: %s' % new.name)

                return results
            except:
                log.error('Failed to parse XML response from newzbin2.es: %s' % traceback.format_exc())

        return results

    def download(self, id):
        try:
            log.info('Download nzb from newzbin, report id: %s ' % id)
            newzbindata = urllib.urlencode({
                'username' : self.conf('username'),
                'password' : self.conf('password'),
                'reportid' : str(id)
            })
            nzburl = urllib2.Request(self.downloadUrl, newzbindata)

            return urllib2.urlopen(nzburl).read().strip()
        except Exception, e:
            log.error('Failed downloading from newzbin, check credit: %s' % e)
            return False

    def getFormatId(self, format):
        for id, quality in self.formatIds.iteritems():
            for q in quality:
                if q == format:
                    return id

        return self.catBackupId
