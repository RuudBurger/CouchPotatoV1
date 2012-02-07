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
    
    def setResponseFormat(self, WebHeader=None, WebFooter=None, Header=None, Footer=None, OpenTag=None, CloseTag=None, CloseFinalTag=None, OpenRecordSet=None, CloseRecordSet=None, OpenRecord=None, CloseRecord=None, OpenField=None, CloseField=None):
        '''See: http://wiki.xbmc.org/index.php?title=Web_Server_HTTP_API#Commands_that_Retrieve_Information'''
        if not self.enabled:
            return
        
        arguments = locals()

        booleans = ["WebHeader", "WebFooter", "CloseFinalTag"]
        setResponseFormatCmds = []
        while arguments:
            k,v = arguments.popitem()
            if k == 'self':
                continue
            elif k in booleans:           
                if v is not None and type(v) is bool:
                    setResponseFormatCmds += [k, " %s" % str(v)]
            else:
                if v is not None:
                    setResponseFormatCmds += [k, " %s" % str(v)] # XBMC expects space after ;
        
        MAX_PARAS = 20 # We have to page here because XBMC has a cap on the # of params it can handle. This number better be even! 
        for page in xrange(0, (len(setResponseFormatCmds)+(MAX_PARAS-1))/MAX_PARAS):
            start = page * MAX_PARAS
            end = min((page + 1) * MAX_PARAS, len(setResponseFormatCmds))
            setResponseFormatCmdStr = ";".join(setResponseFormatCmds[start:end])
        
            for curHost in self.hosts:
                command = {'command': 'SetResponseFormat(%s)' % setResponseFormatCmdStr}
                response = self.send(command, curHost)
                
                log.debug("%s: %s -> %s" % (curHost, setResponseFormatCmdStr, response))
            
    def resetResponseFormat(self):
        '''SetResponseFormat without any parameters returns the formatting to the default values (as would restarting xbmc).'''
        self.setResponseFormat()
        
    def queryVideoDatabase(self, query):
        if not self.enabled:
            return
        
        self.resetResponseFormat()
        self.setResponseFormat(WebHeader=False, WebFooter=False, Header="", Footer="", OpenTag="", CloseTag="", CloseFinalTag=True, OpenRecordSet="", CloseRecordSet="", OpenRecord="<record>", CloseRecord="</record>", OpenField="<field>", CloseField="</field>")

        ret = []
        for curHost in self.hosts:
            command = {'command': 'QueryVideoDatabase(%s)' % query}
            
            rawResponse = self.send(command, curHost)
            if rawResponse:
                ret.append(rawResponse)
        
        self.resetResponseFormat()

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
