from app.config.cplog import CPLog
import base64
import cherrypy
import urllib
import urllib2

log = CPLog(__name__)

class XBMC:

    hosts = []
    username = ''
    password = ''

    def __init__(self):
        self.enabled = self.conf('enabled');
        self.hosts = [x.strip() for x in self.conf('host').split(",")]
        self.username = self.conf('username')
        self.password = self.conf('password')
        self.singleupdate = self.conf('updateOneOnly')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('XBMC', options)

    def send(self, command, host):

        url = 'http://%s/xbmcCmds/xbmcHttp/?%s' % (host, urllib.urlencode(command))

        try:
            req = urllib2.Request(url)
            if self.password:
                authHeader = "Basic %s" % base64.encodestring('%s:%s' % (self.username, self.password))[:-1]
                req.add_header("Authorization", authHeader)

            handle = urllib2.urlopen(req, timeout = 10)
            response = handle.read()
        except Exception, e:
            log.error("Couldn't sent command to XBMC. %s" % e)
            return False

        log.info('XBMC notification to %s successful.' % host)
        return response

    def notify(self, message):
        if not self.enabled:
            return

        for curHost in self.hosts:
            command = {'command': 'ExecBuiltIn', 'parameter': 'Notification(CouchPotato, %s)' % message}
            self.send(command, curHost)

    def queryVideoDatabase(self, query):
        if not self.enabled:
            return

        ret = []
        for curHost in self.hosts:
            command = {'command': 'QueryVideoDatabase(%s)' % query}
            response = self.send(command, curHost).replace("<html>", "").replace("</html>", "")
            ret.append(response)

        return ret

    def updateLibrary(self):
        if not self.enabled:
            return

        updateCommand = {'command': 'ExecBuiltIn', 'parameter': 'XBMC.updatelibrary(video)'}

        if self.singleupdate:
            hosts = [self.hosts[0]]
        else:
            hosts = self.hosts

        for host in hosts:
            request = self.send(updateCommand, host)

            if not request:
                return False

        log.info('XBMC library update initiated')
        return True

    def test(self, hosts, username, password):

        self.enabled = True
        self.hosts = [x.strip() for x in hosts.split(",")]
        self.username = username
        self.password = password

        self.notify('ZOMG Lazors Pewpewpew!')
