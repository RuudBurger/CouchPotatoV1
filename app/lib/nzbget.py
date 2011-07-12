from app.config.cplog import CPLog
import httplib

from base64 import standard_b64encode
import xmlrpclib
import urllib2
import StringIO, gzip, zlib

log = CPLog(__name__)

class nzbGet():

    config = {}

    def __init__(self, config):
        self.config = config

    def conf(self, option):
        return self.config.get('Nzbget', option)

    def send(self, nzb):
        log.info("Sending '%s' to nzbGet." % nzb.name)

        if self.isDisabled():
            log.error("Config properties are not filled in correctly.")
            return False

        nzbGetXMLrpc = "http://nzbget:%(password)s@%(host)s/xmlrpc"
        if self.conf('host') == None:
            log.error("No nzbGet host found in configuration. Please configure it.")
            return False

        url = nzbGetXMLrpc % {"host": self.conf('host'), "password": self.conf('password')}

        nzbGetRPC = xmlrpclib.ServerProxy(url)
        try:
            if nzbGetRPC.writelog("INFO", "CouchPotato connected to drop off %s." % (nzb.name + ".nzb")):
                log.info("Successfully connected to nzbGet")
            else:
                log.info("Successfully connected to nzbGet, but unable to send a message")
        except httplib.socket.error:
            log.error("nzbGet is not responding. Please ensure that nzbGet is running and that your password and host is correct.")
            return False
        except xmlrpclib.ProtocolError, e:
            if e.errmsg == "Unauthorized":
                log.error("nzbGet password is incorrect.")
            else:
                log.error("Protocol Error: " + e.errmsg)
            return False

        try:
            r = urllib2.urlopen(nzb.url).read().strip()
        except:
            log.error("Unable to get NZB file.")

        nzbcontent64 = standard_b64encode(r)

        if nzbGetRPC.append(nzb.name + ".nzb", self.conf('category'), False, nzbcontent64):
            log.info("NZB sent successfully to nzbGet")
            return True
        else:
            log.error("nzbGet could not add %s to the queue" % (nzb.name + ".nzb"))
            return False

    def isDisabled(self):
        if self.conf('host'):
            return False
        else:
            return True
