from app.config.cplog import CPLog
import cherrypy
import urllib
import csv
import time

log = CPLog(__name__)

def conf(options):
    return cherrypy.config['config'].get('IMDBWatchlist', options)

class ImdbWl:
    ''' Downloads and parses IMDB watchlist CSV into list of dicts: [{imdb, title}] '''

    def __init__(self):
        self.enabled = conf('enabled')


    def _get_watchlist(self, url):
        temp_wl = []

        try:
            log.info('Retrieving IMDB Watchlist CSV from %s' % url)
            
            # Just a sanity check in case of bogus parameters
            if not url.startswith('http://'):
                log.info('Incorrect IMDB watchlist URL: %s. Skipping.' % url)
                return temp_wl

            # Check if user has provided watchlist webpage, rather than export URL
            try:
                url_parts = url.split("/")
                if url_parts[3] == "user" and url_parts[5].startswith("watchlist"):
                    url = "http://www.imdb.com/list/export?list_id=watchlist&author_id=%s" % (url_parts[4])
            except(IndexError):
                pass

            urllib._urlopener = ImdbUrlOpener()
            tmp_csv, headers = urllib.urlretrieve(url)
            csvwl = csv.reader(open(tmp_csv, 'rb'))

            for row in csvwl:
                # Check if row is watchlist CSV - should have more than ten fields
                if len(row) > 10:
                    if row[0] != 'position':
                        # log.info('Row is %s' % row)
                        movie = {}
                        movie['imdb'] = row[1]
                        movie['title'] = '%s (%s)' % (row[5], row[10]) 
                        
                        temp_wl.append(movie)
                else:
                    # Row is not from proper watchlist CSV, stop processing this URL
                    log.info('This does not look like a proper IMDB watchlist CSV, skipping.')
                    return temp_wl

        except(IOError):
            log.info('Failed downloading/parsing IMDB Watchlist CSV from %s. Not adding that watchlist to CP' % url)

        return temp_wl


    def _call(self, urls = None):
        if not self.enabled:
            return []

        if not urls:
            urls = conf('url')
        
        # If urls are not defined and not passed as parameters - there is nothing to do here
        if not urls:
            return []

        # Clean urls string and convert it to a list
        urls_list = urls.replace(' ', '').replace('\n','').split(',')

        watchlist = []

        for url in urls_list:
            # Wait a bit, so IMDB will be happy
            log.info('Sleeping before fetching IMDB Watchlist CSV')
            time.sleep(10)

            wl = self._get_watchlist(url)

            # We don't need to have any empty entries in a list in case something went wrong
            if len(wl):
                watchlist.extend(wl)
                
        return watchlist


    def getWatchlists(self):
        return self._call()
    
class ImdbUrlOpener(urllib.FancyURLopener):
    version = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'
