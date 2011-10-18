from app.config.cplog import CPLog
from app.config.db import Session as Db, QualityTemplate, Movie
from app.controllers.movie import MovieController
from app.lib.cron.base import cronBase
from app.lib.library import Library
from app.lib.provider.rss import rss
import time
import datetime
import traceback

log = CPLog(__name__)


class KinepolisRSSCron(cronBase, Library, rss):

    ''' Cronjob for getting top 10 Kinepolis releases '''

    lastChecked = 0
    intervalSec = 86400
    config = {}
    KinepolisRSSUrl = "http://www.kinepolis.com/feed/be/nl/movietop10.xml"
    ComingSoonUrl = "http://www.kinepolis.com/feed/be/nl/new_movies.xml"

    def conf(self, option):
        return self.config.get('KinepolisRSS', option)

    def run(self):
        log.info('Kinepolis RSS thread is running.')

        wait = 0.1 if self.debug else 5

        time.sleep(10)
        while True and not self.abort:
            now = time.time()

            if (self.lastChecked + self.intervalSec) < now:
                try:
                    self.running = True
                    self.lastChecked = now
                    self.doRSSCheck(self.KinepolisRSSUrl)
                    self.doRSSCheck(self.ComingSoonUrl)
                    self.running = False
                except:
                    log.error("!!Uncaught exception in Kinepolis RSS thread: %s" % traceback.format_exc())

            time.sleep(wait)

    def isDisabled(self):
        return not self.conf('enabled')

    def doRSSCheck(self, rssurl):
        '''
        Go find movies and add them!
        '''

        if self.isDisabled():
            log.info('Kinepolis RSS has been disabled')
            return

        log.info('Starting Kinepolis RSS check')

        if not self.isAvailable(self.KinepolisRSSUrl):
            log.info('Kinepolis RSS is not available')
            return

        RSSData = self.urlopen(rssurl)
        RSSItems = self.getItems(RSSData)

        RSSMovies = []
        RSSMovie = {'name': 'test', 'year' : '2009'}

        MyMovieController = MovieController()

        for RSSItem in RSSItems:
            if self.gettextelement(RSSItem, "title").find("Kinepolis Top 10") == -1:
                if rssurl == self.KinepolisRSSUrl:
                    RSSMovie['name'] = self.gettextelement(RSSItem, "title").lower().split(".")[1].rstrip()
                else:
                    RSSMovie['name'] = self.gettextelement(RSSItem, "title").lower().rstrip(" ov")
                currentYear = datetime.datetime.now().strftime("%Y")
                RSSMovie['year'] = currentYear

            if not RSSMovie['name'].find("/") == -1: # make sure it is not a double movie release
                continue

            if int(RSSMovie['year']) < int(self.conf('minyear')): #do year filtering
                continue

            for test in RSSMovies:
                if test.values() == RSSMovie.values(): # make sure we did not already include it...
                    break
            else:
                log.info('Release found: %s.' % RSSMovie)
                RSSMovies.append(RSSMovie.copy())

        if not RSSMovies:
            log.info('No movies found.')
            return

        log.info("Applying IMDB filter to found movies...")

        for RSSMovie in RSSMovies:
            if self.abort: #this loop takes a while, stop when the program needs to close
                return

            time.sleep(5) # give the system some slack

            log.debug('Searching for "%s".' % RSSMovie)
            result = self.searcher['movie'].find(RSSMovie['name'] + ' ' + RSSMovie['year'], limit = 1)

            if not result:
                log.info('Movie not found: "%s".' % RSSMovie)
                continue

            try:
                imdbmovie = self.searcher['movie'].imdb.findByImdbId(result.imdb, True)
            except:
                log.info('Cannot find movie on IMDB: "%s".' % RSSMovie)
                continue

            if not (imdbmovie.get('kind') == 'movie'):
                log.info('This is a ' + imdbmovie.get('kind') + ' not a movie: "%s"' % RSSMovie)
                continue

            if not imdbmovie.get('year'):
                log.info('IMDB has trouble with the year, skipping: "%s".' % RSSMovie)
                continue

            if not int(imdbmovie.get('year')) == int(RSSMovie['year']):
                log.info('IMDB movie year is wrong for: "%s".' % RSSMovie)
                continue

            if not imdbmovie.get('rating'):
                log.info('Rating is unknown for this movie: "%s".' % RSSMovie)
                continue

            if not imdbmovie.get('votes'):
                log.info('Number of votes is unknown for this movie: "%s".' % RSSMovie)
                continue

            if float(imdbmovie.get('rating')) < float(self.conf('minrating')):
                log.info('Rating is too low for this movie: "%s".' % RSSMovie)
                continue

            if float(imdbmovie.get('votes')) < float(self.conf('minvotes')):
                log.info('Number of votes is too low for this movie: "%s".' % RSSMovie)
                continue
                
            log.info('Adding movie to queue: %s.' % imdbmovie.get('title') + ' (' + str(imdbmovie.get('year')) + ') Rating: ' + str(imdbmovie.get('rating')))
            try:
                # Check and see if the movie is in CP already, if so, ignore it.
                cpMovie = Db.query(Movie).filter_by(imdb = result.imdb).first()
                if cpMovie:
                    log.info('Movie found in CP Database, ignore: "%s".' % RSSMovie)
                    continue

                quality = Db.query(QualityTemplate).filter_by(name = self.config.get('Quality', 'default')).one()
                MyMovieController._addMovie(result, quality.id)
            except:
                log.info('MovieController unable to add this movie: "%s". %s' % (RSSMovie, traceback.format_exc()))

def startKinepolisRSSCron(config, searcher, debug):
    cron = KinepolisRSSCron()
    cron.config = config
    cron.searcher = searcher
    cron.debug = debug
    cron.start()

    return cron
