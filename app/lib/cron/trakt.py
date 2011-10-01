from app.config.cplog import CPLog
from app.config.db import Session as Db, QualityTemplate, Movie
from app.controllers.movie import MovieController
from app.lib.cron.base import cronBase
from app.lib.library import Library
import time
import traceback
import urllib2
import json

log = CPLog(__name__)


class TraktCron(cronBase, Library):

    ''' Cronjob for getting trakt watchlist '''

    lastChecked = 0
    intervalSec = 86400
    config = {}
    TraktUrl = "http://api.trakt.tv/user/watchlist/movies.json/"

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
        return not self.conf('enabled')

    def doJSONCheck(self):
        '''
        Go find movies and add them!
        '''

        if self.isDisabled():
            log.info('Trakt has been disabled')
            return

        log.info('Starting Trakt check')
        try:
            url = urllib2.urlopen(self.TraktUrl + self.conf('apikey') + "/" + self.conf('username'), timeout = 10)
            watchlist = json.load(url)
        except (IOError, URLError):
            log.info('Trakt conection failed')
            return

        MyMovieController = MovieController()
        
        if not watchlist:
            log.info('No movies found.')
            return

        for movie in watchlist:
            if self.abort: #this loop takes a while, stop when the program needs to close
                return

            time.sleep(5) # give the system some slack
            
            log.info('Searching for movie: "%s".' % movie.get('title'))
            result = self.searcher['movie'].findByImdbId(movie.get('imdb_id'))
            if not result:
                log.info('Movie not found: "%s".' % movie.get('title'))
                continue
            log.info('Adding movie to queue: %s.' % movie.get('title') + ' (' + str(movie.get('year')) + ')')
            try:
                # Check and see if the movie is in CP already, if so, ignore it.
                cpMovie = Db.query(Movie).filter_by(imdb = movie.get('imdb_id')).first()
                if cpMovie:
                    log.info('Movie found in CP Database, ignore: "%s".' % movie.get('title'))
                    continue
                
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
