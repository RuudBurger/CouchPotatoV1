from app.config.cplog import CPLog
from app.config.db import Session as Db, QualityTemplate, Movie
from app.controllers.movie import MovieController
from app.lib.cron.base import cronBase
from app.lib.library import Library
from app.lib.imdbwl import ImdbWl
import time
import traceback

log = CPLog(__name__)

class ImdbWlCron(cronBase, Library):
    ''' Cronjob for getting imdb watchlist '''

    lastChecked = 0
    intervalSec = 1800
    config = {}

    def conf(self, option):
        return self.config.get('IMDBWatchlist', option)

    def run(self):
        log.info('IMDB watchlist thread is running.')

        wait = 0.1 if self.debug else 5

        time.sleep(10)
        while True and not self.abort:
            now = time.time()

            if (self.lastChecked + self.intervalSec) < now:
                try:
                    self.running = True
                    self.lastChecked = now
                    self.doCsvCheck()
                    self.running = False
                except:
                    log.error("!!Uncaught exception in IMDB Watchlist thread: %s" % traceback.format_exc())

            time.sleep(wait)

    def isDisabled(self):
        return not self.conf('enabled')

    def doCsvCheck(self):
        '''
        Go find movies and add them!
        '''

        if self.isDisabled():
            log.debug('IMDB Watchlist has been disabled')
            return

        log.info('Starting IMDB Watchlist check')
        wl = ImdbWl()
        # Retrieve defined watchlists into one list
        watchlist = wl.getWatchlists()
        if not watchlist:
            log.info("Could not get any info from IMDB Watchlists. Check log for more information.")
            return

        # log.info('Watchlist is "%s"' % watchlist)

        MyMovieController = MovieController()

        for movie in watchlist:
            if self.abort: #this loop takes a while, stop when the program needs to close
                log.info('Aborting IMDB watchlist check')
                return

            time.sleep(5) # give the system some slack

            log.debug('Searching for movie: "%s".' % movie['title'])
            result = False
            try:
                result = self.searcher['movie'].findByImdbId(movie['imdb'])
            except Exception:
                result = False
            if not result:
                log.info('Movie not found: "%s".' % movie['title'])
                continue
            try:
                # Check and see if the movie is in CP already, if so, ignore it.
                cpMovie = Db.query(Movie).filter_by(imdb = movie['imdb']).first()
                if cpMovie:
                    log.info('IMDB Watchlist: Movie found in CP Database, ignore: "%s".' % movie['title'])
                    continue
                log.info('Adding movie to queue: %s.' % movie['title'])
                quality = Db.query(QualityTemplate).filter_by(name = self.config.get('Quality', 'default')).one()
                MyMovieController._addMovie(result, quality.id)
            except:
                log.info('MovieController unable to add this movie: "%s". %s' % (movie['title'], traceback.format_exc()))
        log.info('Finished processing IMDB Watchlist(s)')

def startImdbWlCron(config, searcher, debug):
    cron = ImdbWlCron()
    cron.config = config
    cron.searcher = searcher
    cron.debug = debug
    cron.start()

    return cron
