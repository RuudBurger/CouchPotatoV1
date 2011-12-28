from app.config.cplog import CPLog
from app.config.db import Session as Db, QualityTemplate, Movie
from app.controllers.movie import MovieController
from app.lib.cron.base import cronBase
from app.lib.library import Library
from app.lib.trakt import Trakt
import time
import traceback

log = CPLog(__name__)


class TraktCron(cronBase, Library):

    ''' Cronjob for getting trakt watchlist '''

    lastChecked = 0
    intervalSec = 1800
    config = {}

    def conf(self, option):
        return self.config.get('Trakt', option)

    def run(self):
        log.info('Trakt watchlist thread is running.')

        wait = 0.1 if self.debug else 5

        time.sleep(10)
        while True and not self.abort:
            now = time.time()

            if (self.lastChecked + self.intervalSec) < now:
                try:
                    self.running = True
                    self.lastChecked = now
                    self.doJSONCheck()
                    self.running = False
                except:
                    log.error("!!Uncought exception in Trakt thread: %s" % traceback.format_exc())

            time.sleep(wait)

    def isDisabled(self):
        return not self.conf('watchlist_enabled')

    def doJSONCheck(self):
        '''
        Go find movies and add them!
        '''

        if self.isDisabled():
            log.debug('Trakt has been disabled')
            return

        log.info('Starting Trakt check')
        trakt = Trakt()
        watchlist = trakt.getWatchlist()
        if not watchlist:
            log.info("Could not get watchlist. Please add a password if you have a protected account")
            return

        MyMovieController = MovieController()

        for movie in watchlist:
            if self.abort: #this loop takes a while, stop when the program needs to close
                log.info('Aborting trakt watchlist check')
                return

            time.sleep(5) # give the system some slack
            if (self.conf('dontaddcollection')):
                if ("in_collection" in movie):
                    if (movie.get("in_collection")):
                        log.debug('Movie "%s" already in collection, ignoring' % movie.get('title'))
                        continue

            log.debug('Searching for movie: "%s".' % movie.get('title'))
            result = False
            try:
                if movie.get('tmdb_id') != "":
                    result = self.searcher['movie'].findById(movie.get('tmdb_id'))
                elif movie.get('imdb_id') != "":
                    result = self.searcher['movie'].findByImdbId(movie.get('imdb_id'))
                else:
                    log.info('Trakt has no tmdb or imdb Id for movie: "%s".' % movie.get('title'))
                    continue
            except Exception:
                result = False
            if not result:
                log.info('Movie not found: "%s".' % movie.get('title'))
                continue
            log.debug('Checking movie: %s.' % movie.get('title') + ' (' + str(movie.get('year')) + ')')
            try:
                # Check and see if the movie is in CP already, if so, ignore it.
                cpMovie = Db.query(Movie).filter_by(imdb = movie.get('imdb_id')).first()
                if cpMovie:
                    log.debug('Movie found in CP Database, ignore: "%s".' % movie.get('title'))
                    continue
                log.info('Adding movie to queue: %s.' % movie.get('title') + ' (' + str(movie.get('year')) + ')')
                quality = Db.query(QualityTemplate).filter_by(name = self.config.get('Quality', 'default')).one()
                MyMovieController._addMovie(result, quality.id)
            except:
                log.info('MovieController unable to add this movie: "%s". %s' % (movie.get('title'), traceback.format_exc()))

def startTraktCron(config, searcher, debug):
    cron = TraktCron()
    cron.config = config
    cron.searcher = searcher
    cron.debug = debug
    cron.start()

    return cron
