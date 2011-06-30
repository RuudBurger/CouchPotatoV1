from app.config.cplog import CPLog
from app.lib.provider.yarr.base import nzbBase
from dateutil.parser import parse
from urllib import urlencode
from urllib2 import URLError
import time
import traceback

log = CPLog(__name__)

class nzbsRus(nzbBase):
    """Api for NZBs'R'US"""
    
    name = 'NZBsRUS'

    searchUrl = 'https://www.nzbsrus.com/rssfeed.php'
    
    catIds = {
        12:['1080p'], # sub
        11:['720p'],  #sub
        13:['brrip'], #sub
        45:['dvdr'],
        48:['cam','ts','dvdrip','tc','r5','scr']
    }
    subCats = [12,11,13]
    
    catBackupId = 48
    
    timeBetween = 10
    
    def __init__(self, config):
        log.info('Using NZBsRUS provider')
        
        self.config = config
        
    def conf(self, option):
        return self.config.get('NZBsRUS', option)
    
    def enabled(self):
        return self.conf('enabled') and self.config.get('NZB', 'enabled') and self.conf('userid') and self.conf('userhash')
    
    def find(self, movie, quality, type, retry = False):
        
        self.cleanCache()
        
        results = []
        if not self.enabled() or not self.isAvailable(self.searchUrl):
            return results
        
        catId = self.getCatId(type)
        if catId in self.subCats:
            subCatId = self.getCatId(type)
            
        if not subCatId:
            arguments = urlencode({
                    'cat': catId,
                    'i'  :self.conf('userid'),
                    'h'  : self.conf('userhash')
            })
        else:
            arguments = urlencode({
                    'cat': '',
                    'sub': subCatId,
                    'i'  :self.conf('userid'),
                    'h'  : self.conf('userhash')
            })
            
        url = "%s?%s" % (self.searchUrl, arguments)
        cacheId = str(movie.imdb) + '-' + str(catId)
        #singleCat = (len(self.catIds.get(catId)))
        
        try:
            cached = False
            if self.cache.get(cacheId):
                data = True
                cached = True
                log.info('Getting RSS from cache: %s.' % cacheId )
            else:
                log.info('Searching: %s' %url)
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
                    log.debug('No valid xml')
                    return results
                
                for nzb in xml:
                    
                    title = self.gettextelement(nzb, "title")
                    id = self.gettextelement(nzb, "link").split('/')[-2]
                    date = self.gettextelement(nzb, "pubDate")
                    
                    for entry in self.gettextelement(nzb, "description").split('\n'):
                        if 'Size' in entry:
                            size = entry.split('(')[0].replace('Size ', '').strip()
                    
                    link = self.gettextelement(nzb, "link")
                    
                    new = self.feedItem()
                    new.id = id
                    new.type = 'nzb'
                    new.name = title
                    new.date = int(time.mktime(parse(date).timetuple()))
                    new.size = self.parseSize(size)
                    new.url = link
                    new.content = self.gettextelement(nzb,"description")
                    new.score = self.calcScore(new, movie)
                    new.checkNZB = True
                    
                    if new.date > time.time() - (int(self.config.get('NZB', 'retention')) *24 *60*60):
                        if self.isCorrectMovie(new, movie, type, imdbResults = True):
                            results.append(new)
                            log.info('Found: %s' % new.name)
                    else: 
                        log.info('Found outside retention: %s' % new.name)
                        
                return results
            except:
                log.error('Failed to parse XML response from NZBsRUS.com: %s' % traceback.format_exc())
                    