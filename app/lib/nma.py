from app.config.cplog import CPLog
import cherrypy
from pynma import pynma

log = CPLog(__name__)

class NMA:
    
    app_name = 'CouchPotato'
    
    def __init__(self):
        self.enabled = self.conf('enabled')
        self.apikey = self.conf('apikey')
        self.devkey = self.conf('devkey')
        self.priority = self.conf('priority')
    
    def conf(self, options):
        return cherrypy.config['config'].get('NMA', options)
    
    def notify(self,event, message):
        
        if not self.enabled:
            return
        
        batch = False
        
        p = pynma.PyNMA()
        keys = self.apikey.split(',')
        p.addkey(keys)
        p.developerkey(str(self.devkey))
        
        if len(keys) > 1: batch = True
        
        response = p.push(self.app_name, event, message, priority=self.priority, batch_mode=batch)
        
        for key in keys:
            if not response[str(key)]['code'] == u'200':
                log.error('Could not send notification to NotifyMyAndroid (%s). %s' % (key,response[key]['message']))
                
        return response
        
    def test(self, apikey, devkey, priority):
        
        self.enabled = True
        self.apikey = apikey
        self.devkey = devkey
        self.priority = priority
        
        self.notify('CouchPotato Test', 'ZOMG Lazors Pewpewpew')