from app import latinToAscii
from app.config.cplog import CPLog
from app.config.db import Movie, Session as Db, History
from app.lib.cron.base import cronBase
from app.lib.provider.rss import rss
from app.lib.qualities import Qualities
from sqlalchemy.sql.expression import or_
from app.lib import xbmc
from app.lib import prowl
from app.lib.xbmc import XBMC
from app.lib.prowl import PROWL
from app.lib.growl import GROWL
from app.lib.notifo import Notifo
from app.lib.boxcar import Boxcar
from app.lib.nma import NMA
from app.lib.nmwp import NMWP
from app.lib.twitter import Twitter
import cherrypy
import datetime
import os
import time
import urllib

log = CPLog(__name__)

class YarrCron(cronBase, rss):

    ''' Cronjob for searching for nzb/torrents '''

    lastChecked = 0
    provider = None
    sabNzbd = None
    nzbGet = None
    intervalSec = 10
    checkTheseMovies = []
    stop = False

    def run(self):
        log.info('YarrCron thread is running.')

        self.setInterval(self.config.get('Intervals', 'search'))
        self.forceCheck()

        if not self.debug:
            time.sleep(10)

        wait = 0.1 if self.debug else 10
        while True and not self.abort:

            #check single movie
            try:
                for movieId in self.checkTheseMovies:
                    movie = Db.query(Movie).filter_by(id = movieId).one()
                    self._search(movie, True)
                    self.checkTheseMovies.pop(0)
            except Exception, e:
                log.error('Something went wrong with checkTheseMovies: %s' % e)

            #check all movies
            try:
                now = time.time()
                if (self.lastChecked + self.intervalSec) < now: # and not self.debug:
                    self.lastChecked = now
                    self.searchAll()
            except Exception, e:
                log.error('Something went wrong with searchAll: %s' % e)

            time.sleep(wait)

        log.info('YarrCron has shutdown.')

    def setInterval(self, interval):
        self.intervalSec = int(interval) * 60 * 60

    def forceCheck(self, movie = None):
        if movie == None:
            self.lastChecked = time.time() - self.intervalSec + 10
        else:
            self.checkTheseMovies.append(movie)

    def stopCheck(self):
        log.info('Forcing search to stop.')
        self.stop = True

    def searchAll(self):
        log.info('Searching for new downloads, for all movies.')
        self.doCheck()

        #get all wanted movies
        movies = Db.query(Movie).filter(or_(Movie.status == 'want', Movie.status == 'waiting')).all()
        for movie in movies:
            if not self.abort and not self.stop:
                self._search(movie)

        self.doCheck(False)
        log.info('Finished search.')


    def _search(self, movie, force = False):

        # Stop caching ffs!
        Db.expire_all()

        # Check release date and search for appropriate qualities
        preReleaseSearch = False
        dvdReleaseSearch = False
        now = int(time.time())

        # Search all if ETA is unknow, but try update ETA for next time.
        log.debug('Calculate ETA')
        checkETA = False
        if not movie.eta:
            checkETA = True
            preReleaseSearch = True
            dvdReleaseSearch = True
        else:
            # Prerelease 1 week before theaters
            if movie.eta.theater <= now + 604800:
                preReleaseSearch = True

            # dvdRelease 6 weeks before dvd release
            if movie.eta.dvd <= now + 3628800:
                preReleaseSearch = True
                dvdReleaseSearch = True

            # Dvd date is unknown but movie is in theater already
            if movie.eta.dvd == 0 and movie.eta.theater > now:
                dvdReleaseSearch = False

            # Force ETA check
            if movie.eta.lastCheck < now:
                checkETA = True

        # Minimal week interval for ETA check
        if checkETA and self.config.get('MovieETA', 'enabled'):
            cherrypy.config.get('searchers').get('etaQueue').put({'id':movie.id})

        for queue in movie.queue:

            # Movie already found, don't search further
            if queue.completed:
                log.debug('%s already completed for "%s". Not searching for any qualities below.' % (queue.qualityType, movie.name))
                return True

            # only search for active and not completed, minimal 1 min since last search
            if queue.active and not queue.completed and not self.abort and not self.stop:

                #skip if no search is set
                log.debug('Needs a search?')
                if (not ((preReleaseSearch and queue.qualityType in Qualities.preReleases) or (dvdReleaseSearch and not queue.qualityType in Qualities.preReleases))) and not queue.lastCheck < (now - int(self.config.get('Intervals', 'search')) * 7200):
                    continue

                log.debug('Start searching for movie: %s' % movie.name)
                highest = self.provider.find(movie, queue)
                log.debug('End searching for movie: %s' % movie.name)

                #send highest to SABnzbd & mark as snatched
                if highest:
                    log.debug('Found highest')

                    #update what I found
                    queue.name = latinToAscii(highest.name)
                    queue.link = highest.detailUrl
                    Db.flush()

                    waitFor = queue.waitFor * (60 * 60 * 24)

                    if queue.markComplete or (not queue.markComplete and highest.date + waitFor < time.time()):
                        time.sleep(10) # Give these APIs air!
                        if self.config.get('NZB', 'sendTo') == 'Sabnzbd' and highest.type == 'nzb':
                            success = self.sabNzbd.send(highest, movie.imdb)
                        elif self.config.get('NZB', 'sendTo') == 'Nzbget' and highest.type == 'nzb':
                            success = self.nzbGet.send(highest)
                        elif self.config.get('Torrents', 'sendTo') == 'Transmission' and highest.type == 'torrent':
                            success = self.transmission.send(highest, movie.imdb)
                        else:
                            success = self.blackHole(highest)

                    else:
                        success = False
                        log.info('Found %s but waiting for %d hours.' % (highest.name, ((highest.date + waitFor) - time.time()) / (60 * 60)))

                    # Set status
                    if success:
                        log.debug('Success')
                        movie.status = u'snatched' if queue.markComplete else u'waiting'
                        movie.dateChanged = datetime.datetime.now()
                        queue.lastCheck = now
                        queue.completed = True
                        Db.flush()

                        # Add to history
                        h = History()
                        h.movie = movie.id
                        h.value = str(highest.id) + '-' + str(highest.size)
                        h.status = u'snatched'
                        Db.add(h)
                        Db.flush()

                        # Notify PROWL
                        if self.config.get('PROWL', 'onSnatch'):
                            log.debug('PROWL')
                            prowl = PROWL()
                            prowl.notify(highest.name, 'Download Started')

                        # Notify XBMC
                        if self.config.get('XBMC', 'onSnatch'):
                            log.debug('XBMC')
                            xbmc = XBMC()
                            xbmc.notify('Snatched %s' % highest.name)

                        # Notify GROWL
                        if self.config.get('GROWL', 'onSnatch'):
                            log.debug('GROWL')
                            growl = GROWL()
                            growl.notify('Snatched %s' % highest.name, 'Download Started')

                        # Notify Notifo
                        if self.config.get('Notifo', 'onSnatch'):
                            log.debug('Notifo')
                            notifo = Notifo()
                            notifo.notify('%s' % highest.name, "Snatched:")

                        # Notify Boxcar
                        if self.config.get('Boxcar', 'onSnatch'):
                            log.debug('Boxcar')
                            boxcar = Boxcar()
                            boxcar.notify('%s' % highest.name, "Snatched:")

                        # Notify NotifyMyAndroid
                        if self.config.get('NMA', 'onSnatch'):
                            log.debug('NotifyMyAndroid')
                            nma = NMA()
                            nma.notify('Download Started', 'Snatched %s' % highest.name)
                        
                        # Notify NotifyMyWindowsPhone
                        if self.config.get('NMWP', 'onSnatch'):
                            log.debug('NotifyMyWindowsPhone')
                            nmwp = NMWP()
                            nmwp.notify('Download Started', 'Snatched %s' % highest.name)
                            
                        # Notify Twitter
                        if self.config.get('Twitter', 'onSnatch'):
                            log.debug('Twitter')
                            twitter = Twitter()
                            twitter.notify('Download Started', 'Snatched %s' % highest.name)

                    return True

                queue.lastCheck = now
                Db.flush()

        return False

    def blackHole(self, item):
        blackhole = self.config.get('NZB', 'blackhole') if item.type == 'nzb' else self.config.get('Torrents', 'blackhole')
        if not blackhole or not os.path.isdir(blackhole):
            log.error('No directory set for blackhole %s download.' % item.type)
        else:
            fullPath = os.path.join(blackhole, self.toSaveString(item.name) + '.' + item.type)

            if not os.path.isfile(fullPath):
                if item.download:
                    file = item.download(item.id)

                    if not file:
                        return False
                else:
                    file = urllib.urlopen(item.url).read()

                    if item.type == 'nzb' and "DOCTYPE nzb" not in file:
                        fullPath = os.path.join(blackhole, self.toSaveString(item.name) + '.' + 'rar')

                    log.info('Downloading %s to %s.' % (item.type, fullPath))
                    with open(fullPath, 'wb') as f:
                        f.write(file)

                return True
            else:
                log.error('File %s already exists.' % fullPath)

        return False

    def doCheck(self, bool = True):
        self.running = bool
        self.lastChecked = time.time()
        self.stop = False

    def isChecking(self):
        return self.running

    def lastCheck(self):
        return self.lastChecked

    def nextCheck(self):

        seconds = int((self.lastChecked + self.intervalSec) - time.time())
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)

        ds = ''
        if w > 0:
            ds += '%d week%s' % (w, 's' if w != 1 else '')
        if d > 0:
            ds += '%d day%s' % (d, 's' if d != 1 else '')
        if h > 0:
            ds += '%d hour%s' % (h, 's' if h != 1 else '')
        if m > 0:
            ds += ' %d minute%s' % (m, 's' if m != 1 else '')
        if s > 0 and not h > 0 and not m > 15:
            ds += ' %d second%s' % (s, 's' if s != 1 else '')

        return {
            'seconds': seconds,
            'string': ds
        }

def startYarrCron(config, debug, provider):
    cron = YarrCron()
    cron.config = config
    cron.debug = debug
    cron.provider = provider
    cron.start()

    return cron
