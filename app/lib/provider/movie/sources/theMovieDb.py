from app.config.cplog import CPLog
from app.lib.provider.movie.base import movieBase
from imdb import IMDb
from urllib import quote_plus
from urllib2 import URLError
import cherrypy
import os
import urllib2

log = CPLog(__name__)

class theMovieDb(movieBase):
    """Api for theMovieDb"""

    apiUrl = 'http://api.themoviedb.org/2.1'
    imageUrl = 'http://hwcdn.themoviedb.org'

    def __init__(self, config):
        log.info('Using TheMovieDb provider.')
        self.config = config

    def conf(self, option):
        return self.config.get('TheMovieDB', option)

    def find(self, q, limit = 8, alternative = True):
        ''' Find movie by name '''

        if self.isDisabled():
            return False

        log.debug('TheMovieDB - Searching for movie: %s' % q)

        url = "%s/%s/en/xml/%s/%s" % (self.apiUrl, 'Movie.search', self.conf('key'), quote_plus(self.toSearchString(q)))

        log.info('Searching: %s' % url)

        data = urllib2.urlopen(url, timeout = self.timeout)

        return self.parseXML(data, limit, alternative = alternative)

    def findById(self, id):
        ''' Find movie by TheMovieDB ID '''

        if self.isDisabled():
            return False

        results = self.parseXML(self.getXML(id), limit = 8)

        return results.pop(0)

    def findByImdbId(self, id):
        ''' Find movie by IMDB ID '''

        if self.isDisabled():
            return False

        url = "%s/%s/en/xml/%s/%s" % (self.apiUrl, 'Movie.imdbLookup', self.conf('key'), id)

        try:
            data = urllib2.urlopen(url, timeout = self.timeout)
        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return []

        results = self.parseXML(data, limit = 8, alternative = False)

        if results:
            return results.pop(0)
        else:
            return []

    def parseXML(self, data, limit, alternative = True):
        if data:
            log.debug('TheMovieDB - Parsing RSS')
            try:
                xml = self.getItems(data, 'movies/movie')

                results = []
                nr = 0
                for movie in xml:
                    id = int(self.gettextelement(movie, "id"))

                    name = self.gettextelement(movie, "name")
                    imdb = self.gettextelement(movie, "imdb_id")
                    year = str(self.gettextelement(movie, "released"))[:4]

                    # 1900 is the same as None
                    if year == '1900':
                        year = 'None'

                    # do some IMDB searching if needed
                    if year == 'None':
                        i = IMDb('mobile')
                        if imdb:
                            log.info('Found movie, but with no date, getting data from %s.' % imdb)
                            r = i.get_movie(imdb.replace('tt', ''))
                            year = r.get('year', None)
                        else:
                            log.info('Found movie, but with no date, searching IMDB.')
                            r = i.search_movie(name)
                            if len(r) > 0:
                                imdb = 'tt' + r[0].movieID
                                year = r[0].get('year', None)

                    results.append(self.fillFeedItem(id, name, imdb, year))

                    alternativeName = self.gettextelement(movie, "alternative_name")
                    if alternativeName and alternative:
                        if alternativeName.lower() != name.lower() and alternativeName.lower() != 'none' and alternativeName != None:
                            results.append(self.fillFeedItem(id, alternativeName, imdb, year))

                    nr += 1
                    if nr == limit:
                        break

                log.info('TheMovieDB - Found: %s' % results)
                return results
            except SyntaxError:
                log.error('TheMovieDB - Failed to parse XML response from TheMovieDb')
                return False

    def getXML(self, id):

        if self.isDisabled():
            return False

        url = "%s/%s/en/xml/%s/%s" % (self.apiUrl, 'Movie.getInfo', self.conf('key'), id)
        data = urllib2.urlopen(url, timeout = self.timeout)

        return data

    def saveImage(self, url, destination):

        if url[:6] != 'http://':
            url = self.imageUrl + url

        # Make dir
        imageCache = os.path.join(cherrypy.config.get('cachePath'), 'images')
        if not os.path.isdir(imageCache):
            os.mkdir(imageCache)

        # Return old
        imageFile = os.path.join(imageCache, destination)
        if not os.path.isfile(imageFile):

            try:
                data = urllib2.urlopen(url, timeout = 10)

                # Write file
                with open(imageFile, 'wb') as f:
                    f.write(data.read())

            except (IOError, URLError):
                log.error('Failed get thumb %s.' % url)
                return False

        return 'cache/images/' + destination

    def fillFeedItem(self, id, name, imdb, year):

        item = self.feedItem()
        item.id = id
        item.name = self.toSaveString(name)
        item.imdb = imdb
        item.year = year

        return item

    def isDisabled(self):
        if self.conf('key') == '':
            log.error('TheMovieDB - No API key provided for TheMovieDB')
            True
        else:
            False

    def findReleaseDate(self, movie):
        pass
