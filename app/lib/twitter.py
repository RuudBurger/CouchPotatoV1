from app.config.cplog import CPLog

import cherrypy
import urllib
import oauth2 as oauth
import pythontwitter as twitter

try:
    from urlparse import parse_qsl #@UnusedImport
except:
    from cgi import parse_qsl #@Reimport

log = CPLog(__name__)

class Twitter:

    consumer_key = "OzYPCnKBIW7sLh3MOYCw"
    consumer_secret = "VATWCcvy0kK0wGyyu9phFeMgTn4t1O4yaklEzaXfDqM"

    REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
    ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
    AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

    def __init__(self):
        self.enabled = self.get_conf('enabled')
        self.username = self.get_conf('username')
        self.password = self.get_conf('password')
        self.isAuthenticated = self.get_conf('isAuthenticated')

    def get_conf(self, options):
            return cherrypy.config['config'].get('Twitter', options)

    def set_conf(self, options, value):
        cherrypy.config['config'].set('Twitter', options, value)

    def save_conf(self):
        cherrypy.config['config'].save()

    def notify(self, event, message):
        if not self.enabled or not self.isAuthenticated:
            return

        username = self.consumer_key
        password = self.consumer_secret
        access_token_key = self.get_conf('username')
        access_token_secret = self.get_conf('password')

        log.info('Sending tweet: '+message)

        api = twitter.Api(username, password, access_token_key, access_token_secret)

        try:
            api.PostUpdate('[' + event + '] ' + message)
        except Exception, e:
            log.error('Error sending tweet: '+str(e))
            return False

        log.info('Tweet sent')
        return True

    def test(self):
        self.enabled = True
        self.notify('CouchPotato Test', 'ZOMG Lazors Pewpewpew!')

    def get_authorization(self, referer):

        oauth_consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
        oauth_client = oauth.Client(oauth_consumer)

        log.info('Getting authentication url from Twitter')

        callbackURL = referer + 'twitterAuth/'
        
        resp, content = oauth_client.request(self.REQUEST_TOKEN_URL, 'POST', body=urllib.urlencode({'oauth_callback':callbackURL}))

        if resp['status'] != '200':
            log.error('Invalid response from Twitter requesting temp token: %s: %s' % (resp['status'], content))
        else:
            request_token = dict(parse_qsl(content))

            self.set_conf('username', request_token['oauth_token'])
            self.set_conf('password', request_token['oauth_token_secret'])
            self.save_conf()

            auth_url = self.AUTHORIZATION_URL+"?oauth_token="+ request_token['oauth_token']

            log.info('Your Twitter authentication url is "%s"' % auth_url)
            return auth_url

    def get_credentials(self, key):
            request_token = {}

            request_token['oauth_token'] = self.get_conf('username')
            request_token['oauth_token_secret'] = self.get_conf('password')
            request_token['oauth_callback_confirmed'] = 'true'

            token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
            token.set_verifier(key)

            log.info('Generating and signing request for an access token using key '+key)

            oauth_consumer = oauth.Consumer(key=self.consumer_key, secret=self.consumer_secret)
            oauth_client = oauth.Client(oauth_consumer, token)

            resp, content = oauth_client.request(self.ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % key)

            access_token = dict(parse_qsl(content))

            if resp['status'] != '200':
                log.error('The request for an access token did not succeed: '+str(resp['status']))
                return False
            else:
                log.info('Your Twitter access token is %s' % access_token['oauth_token'])
                log.info('Access token secret is %s' % access_token['oauth_token_secret'])

                self.set_conf('username', access_token['oauth_token'])
                self.set_conf('password', access_token['oauth_token_secret'])
                self.set_conf('isAuthenticated', True)
                self.save_conf()
                return True
