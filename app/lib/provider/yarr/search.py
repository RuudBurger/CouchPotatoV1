from app.config.cplog import CPLog
from app.lib.provider.yarr.sources.newznab import newznab
from app.lib.provider.yarr.sources.nzbmatrix import nzbMatrix
from app.lib.provider.yarr.sources.newzbin import newzbin
from app.lib.provider.yarr.sources.nzbs import nzbs
from app.lib.provider.yarr.sources.tpb import tpb
from app.lib.provider.yarr.sources.x264 import x264
from app.lib.provider.yarr.sources.nzbsrus import nzbsRus
from app.lib.qualities import Qualities
from urllib2 import URLError
import time
import urllib2

log = CPLog(__name__)

class Searcher():

    sources = []

    def __init__(self, config, debug):

        self.config = config
        self.debug = debug

        for yarr in [newzbin, nzbMatrix, nzbs, newznab, tpb, x264, nzbsRus]:
            m = yarr(config)
            self.sources.append(m)

    def find(self, movie, queue):
        ''' Find movie by name '''
        log.debug('Searching for movie: %s' % movie.name)

        qualities = Qualities()

        for source in self.sources:

            results = []

            # find by main name
            type = queue.qualityType
            results.extend(source.find(movie, type, type))

            # Search for alternative naming
            for alt in qualities.getAlternatives(type):
                results.extend(source.find(movie, alt, type))

            #search for highest score
            highest = None
            highestScore = -1000
            if results:
                for result in results:
                    if result.score > highestScore:
                        if not result.checkNZB or self.validNZB(result.url):
                            highest = result
                            highestScore = result.score

                if highest:
                    return highest

        return None

    def validNZB(self, url):

        if self.debug:
            return True

        try:
            time.sleep(10)
            log.info('Checking if %s is valid.' % url)
            data = urllib2.urlopen(url, timeout = 10).info()
            for check in ['nzb', 'download', 'torrent']:
                if check in data.get('Content-Type'):
                    return True

            return False
        except (IOError, URLError):
            return False

    def findById(self, id):
        ''' Find movie by TheMovieDB ID '''

        for source in self.sources:
            result = source.findById(id)
            if result:
                return result

        return []

    def findByImdbId(self, id):
        ''' Find movie by IMDB ID '''

        for source in self.sources:
            result = source.findByImdbId(id)
            if result:
                return result

        return []
