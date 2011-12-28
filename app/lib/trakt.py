from app.config.cplog import CPLog
import base64
import cherrypy
import urllib
import urllib2

from hashlib import sha1

import json

log = CPLog(__name__)

class Trakt:

    watchlist_remove = False
    apikey = ''
    username = ''
    password = ''

    def __init__(self):
        self.enabled = self.conf('notification_enabled');
        self.watchlist_remove = self.conf('watchlist_remove');
        self.username = self.conf('username')
        self.password = self.conf('password')
        self.apikey = self.conf('apikey')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Trakt', options)
    def call(self, method, data = {}):
        log.debug("Call method " + method)

        apikey = self.apikey
        username = self.username
        password = self.password
        password = sha1(password).hexdigest()

        method = method.replace("%API%", apikey)

        data["username"] = username
        data["password"] = password

        encoded_data = json.dumps(data);
        
        try:
            log.info("Calling method http://api.trakt.tv/" + method + ", with data" + encoded_data)
            stream = urllib.urlopen("http://api.trakt.tv/" + method, encoded_data)
            resp = json.load(stream)
        except(IOError):
            log.info("Failed calling method")
            resp = None
        return resp

    def send(self, method, data = {}):
        resp = self.call(method, data)
        if (resp == None):
            return False
        if ("error" in resp):
            log.info("Trakt error message in response: " + resp["error"])
        if (resp["status"] == "success"):
            log.info("Method call successful")
            return True
        else:
            log.info("Method call unsuccessful: " + resp["status"])
            return False

    def notify(self, name, year, imdb_id):
        if not self.enabled:
            return
        
        method = "movie/library/"
        method += "%API%"
        
        data = {
            'movies': [ {
                'imdb_id': imdb_id,
                'title': name,
                'year': year
                } ]
            }
        
        added = self.send(method, data)
        
        if self.watchlist_remove:
            method = "movie/unwatchlist/"
            method += "%API%"
            data = {
                'movies': [ {
                    'imdb_id': imdb_id,
                    'title': name,
                    'year': year
                    } ]
                }
            self.send(method, data)
        
        return added

    def test(self, apikey, username, password):
        self.username = username
        self.password = password
        self.apikey = apikey
        
        method = "account/test/"
        method += "%API%"
        
        return self.send(method)

    def getWatchlist(self):
        method = "user/watchlist/movies.json/%API%/" + self.username
        return self.call(method)