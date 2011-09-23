from app.config.cplog import CPLog
import base64
import cherrypy
import json
import urllib
import urllib2
import time

log = CPLog(__name__)

class Boxcar:

    username = ''
    password = ''

    def __init__(self):
        self.enabled = self.conf('enabled')
        self.username = self.conf('username')
        self.password = self.conf('password')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Boxcar', options)

    def send(self, message, status):

        url = 'https://boxcar.io/notifications'

        try:
            message = message.strip()
            data = urllib.urlencode({
                'notification[from_screen_name]': self.username,
                'notification[message]': message.encode('utf-8'),
                'notification[from_remote_service_id]': int(time.time()),
                'notification[source_url]' : 'nas.local'
            })

            req = urllib2.Request(url)
	    authHeader = "Basic %s" % base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
	    req.add_header("Authorization", authHeader)
	    
            handle = urllib2.urlopen(req, data)
            result = json.load(handle)

            if result['status'] != 'success' or result['response_message'] != 'OK':
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

    def test(self, username, password):

        self.enabled = True
        self.username = username
        self.password = password

        self.notify('This is a test notification from Couch Potato', "Testing:")
