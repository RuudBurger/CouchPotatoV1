from app.config.cplog import CPLog
from app.lib import cleanHost
import transmissionrpc
import re
import os

log = CPLog(__name__)

class transmission():

    config = {}

    def __init__(self, config):
        self.config = config

    def conf(self, option):
        return self.config.get('Transmission', option)

    def send(self, torrent, imdbId=None):
        log.info("Sending '%s' to Transmission." % torrent.name)

        if self.isDisabled():
            log.error("Config properties are not filled in correctly.")
            return False
        
        # Load host from config and split out port.
        host = self.conf('host').split(':')
        if not host[1].isdigit():
            log.error("Config properties are not filled in correctly, port is missing.")
            return False
        
        # Set parameters for Transmission
        params = {}
        change_params = {}
        
        if not (self.conf('ratio') == ''):
            change_params['seedRatioLimit'] = self.conf('ratio')
            change_params['seedRatioMode'] = 1
        
        if not (self.conf('paused') == ''):
            params['paused'] = self.conf('paused')

        if not (self.conf('directory') == ''):
            params['download_dir'] = self.conf('directory')

        try:
            tc = transmissionrpc.Client(host[0], port = host[1], user = self.conf('username'), password = self.conf('password'))
            tr_id = tc.add_uri(torrent.url, **params)
            
            # Change settings of added torrents 
            for item in tr_id:
                try:
                    tc.change(item, timeout=None, **change_params)
                except transmissionrpc.TransmissionError, e:
                    log.error('Failed to change settings for transfer in transmission: ' +str(e))

            return True

        except transmissionrpc.TransmissionError, e:
            log.error('Failed to send link to transmission: ' +str(e))
            return False

    def isDisabled(self):
        if self.conf('host'):
            return False
        else:
            return True