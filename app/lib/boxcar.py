from app.config.cplog import CPLog
import base64
import cherrypy
import json
import urllib
import urllib2
import time
import platform 

log = CPLog(__name__)

class Boxcar:

    username = ''

    def __init__(self):
        self.enabled = self.conf('enabled')
        self.username = self.conf('username')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Boxcar', options)

    def send(self, message, status):
        boxcar_provider_key = '7MNNXY3UIzVBwvzkKwkC' #default for provider as given by Boxcar when CouchPotato was registered
        url = 'https://boxcar.io/devices/providers/' + boxcar_provider_key + '/notifications'
        try:
            message = message.strip()
            data = urllib.urlencode({
                'email': self.username,
                'notification[from_screen_name]': 'CouchPotato running on ' + platform.uname()[1],
                'notification[message]': message.encode('utf-8'),
                'notification[from_remote_service_id]': int(time.time()),
            })

            req = urllib2.Request(url)

            handle = urllib2.urlopen(req, data)
            result = handle.info()
            if result['status'] != '200':
                raise Exception

        except Exception, e:
            log.info(e)
            log.error('Boxcar notification failed.')
            return False

        log.info('Boxcar notification successful.')
        return

    def notify(self, message, status):
        if not self.enabled:
            return

        self.send(message, status)

    def test(self, username):
        self.enabled = True
        self.username = username

        self.notify('This is a test notification from Couch Potato', "Testing:")
