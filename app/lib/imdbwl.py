from app.config.cplog import CPLog
import cherrypy
import urllib
import csv

log = CPLog(__name__)

def conf(options):
    return cherrypy.config['config'].get('IMDBWatchlist', options)

class ImdbWl:

    def __init__(self):
        self.enabled = conf('enabled')

    def call(self, url = None):
        log.debug("Call method")

        if not url:
            url = conf('url')

        watchlist = []
        try:
            log.info('Retrieving IMDB Watchlist CSV from %s' % url)
            urllib._urlopener = ImdbUrlOpener()
            tmp_csv, headers = urllib.urlretrieve(url)
            csvwl = csv.reader(open(tmp_csv, 'rb'))
            for row in csvwl:
                if row[0] != 'position':
                    #log.info('Row is %s' % row)
                    movie = {}
                    movie['imdb'] = row[1]
                    movie['title'] = '%s (%s)' % (row[5], row[10]) 
                    
                    watchlist.append(movie)
        except(IOError):
            log.info("Failed calling downloading/parsing IMDB Watchlist CSV")
            watchlist = None
        return watchlist

    def test(self, url):
        wl = self.call('http://www.imdb.com/list/export?list_id=watchlist&author_id=ur0034213')
        print wl

    def getWatchlist(self):
        return self.call()
    
class ImdbUrlOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'
