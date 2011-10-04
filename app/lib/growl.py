# Based on netprowl by the following authors.

# Altered 1st October 2010 - Tim Child.
# Have added the ability for the command line arguments to take a password.

# Altered 1-17-2010 - Tanner Stokes - www.tannr.com
# Added support for command line arguments

# ORIGINAL CREDITS
# """Growl 0.6 Network Protocol Client for Python"""
# __version__ = "0.6.3"
# __author__ = "Rui Carmo (http://the.taoofmac.com)"
# __copyright__ = "(C) 2004 Rui Carmo. Code under BSD License."
# __contributors__ = "Ingmar J Stein (Growl Team), John Morrissey (hashlib patch)"

from app.config.cplog import CPLog
import socket
import cherrypy
from app.lib.growl_lib import gntp

log = CPLog(__name__)

class GROWL:

    hosts = []
    password = ''

    def __init__(self):
        self.enabled = self.conf('enabled');
        self.hosts = [x.strip() for x in self.conf('host').split(",")]
        self.password = self.conf('password')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('GROWL', options)

    def updateLibrary(self):
        #For uniformity reasons not removed
        return

    def test(self, hosts, password):
        self.enabled = True
        self.hosts = [x.strip() for x in hosts.split(",")]
        self.password = password

        self._sendRegistration('Test')
        return self._sendGrowl("Test Growl", "Testing Growl settings from CouchPotato", "Test", force=True)

    def notify(self, message, title):
        if not self.enabled:
            return
        self._sendGrowl(title, message)

    def _send_growl(self, options, message=None):
                
        #Send Notification
        notice = gntp.GNTPNotice()
    
        #Required
        notice.add_header('Application-Name',options['app'])
        notice.add_header('Notification-Name',options['name'])
        notice.add_header('Notification-Title',options['title'])
    
        if options['password']:
            notice.set_password(options['password'])
    
        #Optional
        if options['sticky']:
            notice.add_header('Notification-Sticky',options['sticky'])
        if options['priority']:
            notice.add_header('Notification-Priority',options['priority'])
        if options['icon']:
            notice.add_header('Notification-Icon', 'https://github.com/RuudBurger/CouchPotato/raw/master/media/images/homescreen.png')
    
        if message:
            notice.add_header('Notification-Text',message)

        response = self._send(options['host'],options['port'],notice.encode(),options['debug'])
        if isinstance(response,gntp.GNTPOK): return True
        return False

    def _send(self, host,port,data,debug=False):
        if debug: print '<Sending>\n',data,'\n</Sending>'
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host,port))
        s.send(data)
        response = gntp.parse_gntp(s.recv(1024))
        s.close()
    
        if debug: print '<Received>\n',response,'\n</Received>'

        return response

    def _sendGrowl(self, title="CouchPotato Notification", message=None, name=None, force=False):
        if name == None:
            name = title
    
        port = 23053
    
        growlHosts = []
        for host in self.hosts:
            growlHosts.append((host, port))
    
        opts = {}
    
        opts['name'] = name
    
        opts['title'] = title
        opts['app'] = 'CouchPotato'
    
        opts['sticky'] = None
        opts['priority'] = None
        opts['debug'] = False
    
        opts['password'] = self.password
    
        opts['icon'] = True
    
        for pc in growlHosts:
            opts['host'] = pc[0]
            opts['port'] = pc[1]
            log.info(u"Sending growl to "+opts['host']+":"+str(opts['port'])+": "+message)
            try:
                return self._send_growl(opts, message)
            except socket.error, e:
                log.error(u"Unable to send growl to "+opts['host']+":"+str(opts['port'])+": "+ex(e))
                return False

    def _sendRegistration(self, name='CouchPotato Notification'):
        opts = {}
    
        port = 23053

        growlHosts = []
        for host in self.hosts:
            growlHosts.append((host, port))
            
        opts['password'] = self.password
        
        opts['app'] = 'CouchPotato'
        opts['debug'] = False
        
        for pc in growlHosts:
            opts['host'] = pc[0]
            opts['port'] = pc[1]

            #Send Registration
            register = gntp.GNTPRegister()
            register.add_header('Application-Name', opts['app'])
            register.add_header('Application-Icon', 'https://github.com/RuudBurger/CouchPotato/raw/master/media/images/homescreen.png')
        
            register.add_notification('Test', True)
            register.add_notification('Download Started', True)
            register.add_notification('Download Complete', True)

            if opts['password']:
                register.set_password(opts['password'])
        
            try:
                log.info(u"Sending growl registration to "+opts['host']+":"+str(opts['port']))
                return self._send(opts['host'],opts['port'],register.encode(),opts['debug'])
            except socket.error, e:
                log.error(u"Unable to send growl to "+opts['host']+":"+str(opts['port'])+": "+str(e).decode('utf-8'))
                return False
