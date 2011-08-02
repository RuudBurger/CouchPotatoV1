from app.config.cplog import CPLog
import cherrypy
import subprocess

log = CPLog(__name__)

class Synoindex:

    def __init__(self):
        self.enabled = self.conf('enabled')
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Synoindex', options)
        
    def addToLibrary(self, folder_name):
        if not self.enabled:
            return
        
        synoindexCommand = ['/usr/syno/bin/synoindex', '-A', folder_name]
        log.info(u"Executing synoindex command: "+str(synoindexCommand))
        try:
            p = subprocess.Popen(synoindexCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out = p.communicate()
            log.info(u"Result from synoindex: "+str(out))
            return True
        except OSError, e:
            log.error(u"Unable to run synoindex: "+str(e))
            return False
