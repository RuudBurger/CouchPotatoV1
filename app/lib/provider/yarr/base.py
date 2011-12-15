from app.config.cplog import CPLog
from app.config.db import Session as Db, History
from app.lib.provider.rss import rss
from app.lib.qualities import Qualities
from sqlalchemy.sql.expression import and_
import re
import time

log = CPLog(__name__)

class nzbBase(rss):

    config = None
    type = 'nzb'
    name = ''

    nameScores = [
        'proper:2', 'repack:2',
        'unrated:1',
        'x264:1',
        'DTS:4', 'AC3:2',
        '720p:10', '1080p:10', 'bluray:10', 'dvd:1', 'dvdrip:1', 'brrip:1', 'bdrip:1',
        'imbt:1', 'cocain:1', 'vomit:1', 'fico:1', 'arrow:1', 'pukka:1', 'prism:1', 'devise:1',
        'metis:1', 'diamond:1', 'wiki:1', 'cbgb:1', 'crossbow:1', 'sinners:1', 'amiable:1', 'refined:1', 'twizted:1', 'felony:1', 'hubris:1', 'machd:1', 
        'german:-10', 'french:-10', 'spanish:-10', 'swesub:-20', 'danish:-10'
    ]

    catIds = {}
    catBackupId = ''

    cache = {}

    sizeGb = ['gb', 'gib']
    sizeMb = ['mb', 'mib']
    sizeKb = ['kb', 'kib']

    def parseSize(self, size):

        sizeRaw = size.lower()
        size = re.sub(r'[^0-9.]', '', size).strip()

        for s in self.sizeGb:
            if s in sizeRaw:
                return float(size) * 1024

        for s in self.sizeMb:
            if s in sizeRaw:
                return float(size)

        for s in self.sizeKb:
            if s in sizeRaw:
                return float(size) / 1024

        return 0

    def calcScore(self, nzb, movie):
        ''' Calculate the score of a NZB, used for sorting later '''

        score = 0
        if nzb.name:
            score = self.nameScore(nzb.name, movie)
            score += self.nameRatioScore(nzb.name, movie.name)

        return score

    def nameScore(self, name, movie):
        ''' Calculate score for words in the NZB name '''

        score = 0
        name = name.lower()

        #give points for the cool stuff
        for value in self.nameScores:
            v = value.split(':')
            add = int(v.pop())
            if v.pop() in name:
                score = score + add

        #points if the year is correct
        if str(movie.year) in name:
            score = score + 1

        # Contains preferred word
        nzbWords = re.split('\W+', self.toSearchString(name).lower())
        preferredWords = self.config.get('global', 'preferredWords').split(',')
        for word in preferredWords:
            if word.strip() and word.strip().lower() in nzbWords:
                score = score + 100

        return score

    def nameRatioScore(self, nzbName, movieName):

        nzbWords = re.split('\W+', self.toSearchString(nzbName).lower())
        movieWords = re.split('\W+', self.toSearchString(movieName).lower())

        # Replace .,-_ with space
        leftOver = len(nzbWords) - len(movieWords)
        if 2 <= leftOver <= 6:
            return 4
        else:
            return 0

    def isCorrectMovie(self, item, movie, qualityType, imdbResults = False, singleCategory = False):

        # Ignore already added.
        if self.alreadyTried(item, movie.id):
            log.info('Already tried this one, ignored: %s' % item.name)
            return False

        def get_words(text):
            return filter(None, re.split('\W+', text.lower()))

        nzbWords = get_words(item.name)
        requiredWords = get_words(self.config.get('global', 'requiredWords'))
        missing = set(requiredWords) - set(nzbWords)
        if missing:
            log.info("NZB '%s' misses the following required words: %s" %
                            (item.name, ", ".join(missing)))
            return False

        ignoredWords = get_words(self.config.get('global', 'ignoreWords'))
        blacklisted = set(ignoredWords).intersection(set(nzbWords))
        if blacklisted:
            log.info("NZB '%s' contains the following blacklisted words: %s" %
                            (item.name, ", ".join(blacklisted)))
            return False

        q = Qualities()
        type = q.types.get(qualityType)

        # Contains lower quality string
        if self.containsOtherQuality(item.name, type, singleCategory):
            log.info('Wrong: %s, contains other quality, looking for %s' % (item.name, type['label']))
            return False

        # Outsize retention
        if item.type is 'nzb':
            if item.date < time.time() - (int(self.config.get('NZB', 'retention')) * 24 * 60 * 60):
                log.info('Found but outside %s retention: %s' % (self.config.get('NZB', 'retention'), item.name))
                return False

        # File to small
        minSize = q.minimumSize(qualityType)
        if minSize > item.size:
            log.info('"%s" is too small to be %s. %sMB instead of the minimal of %sMB.' % (item.name, type['label'], item.size, minSize))
            return False

        # File to large
        maxSize = q.maximumSize(qualityType)
        if maxSize < item.size:
            log.info('"%s" is too large to be %s. %sMB instead of the maximum of %sMB.' % (item.name, type['label'], item.size, maxSize))
            return False

        if imdbResults:
            return True

        # Check if nzb contains imdb link
        if self.checkIMDB([item.content], movie.imdb):
            return True

        # if no IMDB link, at least check year range 1
        if len(movie.name.split(' ')) > 2 and self.correctYear([item.name], movie.year, 1) and self.correctName(item.name, movie.name):
            return True

        # if no IMDB link, at least check year
        if len(movie.name.split(' ')) == 2 and self.correctYear([item.name], movie.year, 0) and self.correctName(item.name, movie.name):
            return True

        log.info("Wrong: %s, undetermined naming. Looking for '%s (%s)'" % (item.name, movie.name, movie.year))
        return False

    def alreadyTried(self, nzb, movie):
        return Db.query(History).filter(and_(History.movie == movie, History.value == str(nzb.id) + '-' + str(nzb.size), History.status == u'ignore')).first()

    def containsOtherQuality(self, name, preferedType, singleCategory = False):

        nzbWords = re.split('\W+', self.toSearchString(name).lower())

        found = {}
        for type in Qualities.types.itervalues():
            # Main in words
            if type['key'].lower() in nzbWords:
                found[type['key']] = True

            # Alt in words
            for alt in type['alternative']:
                if alt.lower() in nzbWords:
                    found[type['key']] = True

        # Allow other qualities
        for allowed in preferedType['allow']:
            if found.get(allowed):
                del found[allowed]

        if (len(found) == 0 and singleCategory):
            return False

        return not (found.get(preferedType['key']) and len(found) == 1)

    def checkIMDB(self, haystack, imdbId):

        for string in haystack:
            if 'imdb.com/title/' + imdbId in string:
                return True

        return False

    def correctYear(self, haystack, year, range):

        for string in haystack:
            if str(year) in string or str(int(year) + range) in string or str(int(year) - range) in string: # 1 year of is fine too
                return True

        return False

    def getCatId(self, prefQuality):
        ''' Selecting category by quality '''

        for id, quality in self.catIds.iteritems():
            for q in quality:
                if q == prefQuality:
                    return id

        return self.catBackupId

    def downloadLink(self, id):
        return self.downloadUrl % (id, self.getApiExt())

    def nfoLink(self, id):
        return self.nfoUrl % id

    def detailLink(self, id):
        return self.detailUrl % id

    def getApiExt(self):
        return ''

    def cleanCache(self):
        try:
            tempcache = {}
            for x, cache in self.cache.iteritems():
                if cache['time'] + 300 > time.time():
                    tempcache[x] = self.cache[x]
                else:
                    log.debug('Removing cache %s' % x)

            self.cache = tempcache
        except:
            self.cache = {}

class torrentBase(nzbBase):

    type = 'torrent'
