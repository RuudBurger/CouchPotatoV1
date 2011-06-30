from app.config.cplog import CPLog
import base64
import cherrypy
import json
import urllib
import urllib2

log = CPLog(__name__)

class Notifo:

    username = ''
    key = ''

    def __init__(self):
        self.enabled = self.conf('enabled')
        self.username = self.conf('username')
        self.key = self.conf('key')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Notifo', options)

    def send(self, message, status):

        url = 'https://api.notifo.com/v1/send_notification'

        try:
            message = message.strip()
            data = urllib.urlencode({
                'label': "CouchPotato",
                'title': status,
                'msg': message.encode('utf-8')
            })

            req = urllib2.Request(url)
	    authHeader = "Basic %s" % base64.encodestring('%s:%s' % (self.username, self.key))[:-1]
	    req.add_header("Authorization", authHeader)

            handle = urllib2.urlopen(req, data)
            result = json.load(handle)

            if result['status'] != 'success' or result['response_message'] != 'OK':
                raise Exception

        except Exception, e:
            log.info(e)
            log.error('Notifo notification failed.')
            return False

        log.info('Notifo notification successful.')
        return

    def notify(self, message, status):
        if not self.enabled:
            return

        self.send(message, status)

    def test(self, username, key):

        self.enabled = True
        self.username = username
        self.key = key

        self.notify('This is a test notification from Couch Potato', "Testing:")
