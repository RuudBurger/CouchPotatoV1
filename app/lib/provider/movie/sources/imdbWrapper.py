from app.config.cplog import CPLog
from app.lib.provider.movie.base import movieBase
from imdb import IMDb

log = CPLog(__name__)

class imdbWrapper(movieBase):
    """Api for theMovieDb"""

    def __init__(self, config, http = True):
        log.info('Using IMDB provider.')

        self.config = config
        if not http:
            self.p = IMDb('mobile')
        else:
            self.p = IMDb('http')

    def conf(self, option):
        return self.config.get('IMDB', option)

    def find(self, q, limit = 8, alternative = True):
        ''' Find movie by name '''

        log.info('IMDB - Searching for movie: %s' % q)

        r = self.p.search_movie(q)

        return self.toResults(r, limit)

    def toResults(self, r, limit = 8, one = False):
        results = []

        if one:
            new = self.feedItem()
            new.imdb = 'tt' + r.movieID
            new.name = self.toSaveString(r['title'])
            try:
                new.year = r['year']
            except:
                new.year = ''

            return new
        else :
            nr = 0
            for movie in r:
                results.append(self.toResults(movie, one = True))
                nr += 1
                if nr == limit:
                    break

            return results

    def findById(self, id):
        ''' Find movie by TheMovieDB ID '''

        return []


    def findByImdbId(self, id, details = False):
        ''' Find movie by IMDB ID '''

        log.info('IMDB - Searching for movie: %s' % str(id))

        r = self.p.get_movie(id.replace('tt', ''))

        if not details:
            return self.toResults(r, one = True)
        else:
            self.p.update(r)
            self.p.update(r, info = 'release dates')
            self.p.update(r, info = 'taglines')
            self.p.update(r, info = 'vote details')
            return r

    def get_IMDb_instance(self):
        return IMDb('http')


    def findReleaseDate(self, movie):
        pass
