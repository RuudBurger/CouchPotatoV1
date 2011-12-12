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
        self.enabled = self.conf('enabled');
        self.watchlist_remove = self.conf('watchlist_remove');
        self.username = self.conf('username')
        self.password = self.conf('password')
        self.apikey = self.conf('apikey')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Trakt_notification', options)

    def send(self, method, data = {}):
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
            resp = stream.read()

            resp = json.loads(resp)
            
            if ("error" in resp):
                raise Exception(resp["error"])
        except (IOError, Exception):
            log.info("Failed calling method")
            return False

        if (resp["status"] == "success"):
            log.info("Method call successful")
            return True

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
        
        return self.send(method, {})
