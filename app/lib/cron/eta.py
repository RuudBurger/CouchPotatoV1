from app.config.cplog import CPLog
from app.config.db import Movie, MovieETA, Session as Db
from app.lib.cron.base import cronBase
from app.lib.provider.rss import rss
from imdb.parser.http.bsouplxml._bsoup import BeautifulSoup, SoupStrainer
from sqlalchemy.sql.expression import or_
from urllib2 import URLError
import Queue
import cherrypy
import re
from dateutil.parser import parse
import time
import urllib
import urllib2

etaQueue = Queue.Queue()
log = CPLog(__name__)

class etaCron(rss, cronBase):

    searchUrl = 'http://videoeta.com/search/'
    detailUrl = 'http://videoeta.com/movie/'

    def run(self):
        log.info('MovieETA thread is running.')

        timeout = 0.1 if self.debug else 1
        while True and not self.abort:
            
            config = cherrpy.config.get('config')
            
            if not config.get('MovieETA','enabled'):
                log.info('MovieETA disabled')
                break
            
            try:
                queue = etaQueue.get(timeout = timeout)
                if queue.get('id'):
                    movie = Db.query(Movie).filter_by(id = queue.get('id')).first()
                else:
                    movie = queue.get('movie')

                if not cherrypy.config.get('debug'):
                    #do a search
                    self.running = True
                    result = self.search(movie)
                    if result:
                        self.save(movie, result)
                    self.running = False

                etaQueue.task_done()
                time.sleep(timeout)
            except Queue.Empty:
                pass

        log.info('MovieETA thread shutting down.')

    def all(self):
        activeMovies = Db.query(Movie).filter(or_(Movie.status == u'want', Movie.status == u'waiting')).all()
        for movie in activeMovies:
            etaQueue.put({'movie':movie})

    def save(self, movie, result):

        row = Db.query(MovieETA).filter_by(movieId = movie.id).first()
        if not row:
            row = MovieETA()
            Db.add(row)

        row.movieId = movie.id
        row.videoEtaId = result.get('id', 0)
        row.theater = result.get('theater', 0)
        row.dvd = result.get('dvd', 0)
        row.bluray = result.get('bluray', 0)
        row.lastCheck = int(time.time())
        Db.flush()

    def search(self, movie, page = 1):

        # Already found it, just update the stuff
        if movie.eta and movie.eta.videoEtaId > 0:
            log.debug('Updating VideoETA for %s.' % movie.name)
            return self.getDetails(movie.eta.videoEtaId)

        # Do search
        log.info('Searching page:%d VideoETA for %s.' % (page, movie.name))
        arguments = urllib.urlencode({
            'search_query':self.toSearchString(movie.name),
            'page': page
        })
        url = "%s?%s" % (self.searchUrl, arguments)

        log.debug('Search url: %s.' % url)

        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return False

        results = self.getItems(data)

        if results:
            for result in results:
                if str(movie.year).lower() != 'none' and self.toSearchString(result.get('name')).lower() == self.toSearchString(movie.name).lower() and result.get('year') == int(movie.year):
                    log.debug('MovieETA perfect match!')
                    return self.getDetails(result.get('id'))

        if page == 1 and len(results) > 29:
            return self.search(movie, page = 2)

        return {}

    def getDetails(self, id):
        url = self.detailUrl + str(id)

        log.info('Scanning %s.' % url)

        try:
            data = urllib2.urlopen(url, timeout = self.timeout).read()
        except (IOError, URLError):
            log.error('Failed to open %s.' % url)
            return False

        # Search for theater release
        theaterDate = 0
        try:
            theaterLink = SoupStrainer('a', href = re.compile('/month_theaters.html\?'))
            theater = BeautifulSoup(data, parseOnlyThese = theaterLink)
            theaterDate = int(time.mktime(parse(theater.a.contents[0]).timetuple()))
        except AttributeError:
            log.debug('No Theater release info found.')

        # Search for dvd release date
        dvdDate = 0
        try:
            try:
                dvdLink = SoupStrainer('a', href = re.compile('/month_video.html\?'))
                dvd = BeautifulSoup(data, parseOnlyThese = dvdLink)
                dvdDate = int(time.mktime(parse(dvd.a.contents[0]).timetuple()))
            except:
                pass

            # Try left column
            if not dvdDate:
                dvdReleases = SoupStrainer('p', text = re.compile('Released'))
                dvd = BeautifulSoup(data, parseOnlyThese = dvdReleases)
                for date in dvd:
                    foundDate = int(time.mktime(parse(date.replace('Released', '')).timetuple()))
                    dvdDate = foundDate if foundDate > dvdDate else dvdDate

        except AttributeError:
            log.debug('No DVD release info found.')

        # Does it have blu-ray release?
        bluray = []
        try:
            bees = SoupStrainer('b')
            soup = BeautifulSoup(data, parseOnlyThese = bees)
            bluray = soup.findAll('b', text = re.compile('Blu-ray'))
        except AttributeError:
            log.info('No Bluray release info found.')

        dates = {
            'id': id,
            'dvd': dvdDate,
            'theater': theaterDate,
            'bluray': len(bluray) > 0
        }
        log.debug('Found: %s' % dates)
        return dates

    def getItems(self, data):

        results = []

        soup = BeautifulSoup(data)
        table = soup.find("table", { "class" : "chart" })

        try:
            for tr in table.findAll("tr"):
                item = {}

                for td in tr.findAll('td'):

                    # Get title and ID from <a>
                    if td.a and not td.a.img:
                        item['id'] = int(td.a['href'].split('/')[-1])
                        item['name'] = str(td.a.contents[0])

                    # Get year from <td>
                    if not td.h3 and not td.a:
                        if len(td.contents) == 1:
                            for y in td.contents:
                                try:
                                    item['year'] = int(y)
                                except ValueError:
                                    pass
                if item:
                    results.append(item)
        except AttributeError:
            log.error('No search results.')

        return results


def startEtaCron(debug):
    c = etaCron()
    c.debug = debug
    c.start()

    return c
