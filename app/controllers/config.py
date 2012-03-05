from app.config.cplog import CPLog
from app.config.db import QualityTemplate, Session as Db
from app.controllers import BaseController, redirect
from app.lib.qualities import Qualities
from app.lib.xbmc import XBMC
from app.lib.nmj import NMJ
from app.lib.plex import PLEX
from app.lib.prowl import PROWL
from app.lib.growl import GROWL
from app.lib.notifo import Notifo
from app.lib.boxcar import Boxcar
from app.lib.nma import NMA
from app.lib.nmwp import NMWP
from app.lib.twitter import Twitter
from app.lib.trakt import Trakt
import cherrypy
import json
import sys

log = CPLog(__name__)

class ConfigController(BaseController):

    @cherrypy.expose
    @cherrypy.tools.mako(filename = "config/index.html")
    def index(self):
        '''
        Config form
        '''
        config = cherrypy.config.get('config')

        renamer = self.cron.get('renamer')
        replacements = {
             'cd': ' cd1',
             'cdNr': ' 1',
             'ext': 'mkv',
             'namethe': 'Big Lebowski, The',
             'thename': 'The Big Lebowski',
             'year': 1998,
             'first': 'B',
             'original': 'The.Big.Lebowski.1998.1080p.BluRay.x264.DTS-GROUP',
             'group':'GROUP',
             'audio':'DTS',
             'video':'x264',
             'quality': '1080p',
             'sourcemedia': 'BluRay',
             'resolution' : '1920x1080'
        }

        trailerFormats = self.cron.get('trailer').formats
        foldernameResult = renamer.doReplace(config.get('Renamer', 'foldernaming'), replacements)
        filenameResult = renamer.doReplace(config.get('Renamer', 'filenaming'), replacements)

        return self.render({'trailerFormats':trailerFormats, 'foldernameResult':foldernameResult, 'filenameResult':filenameResult, 'config':config})

    @cherrypy.expose
    def save(self, **data):
        '''
        Save all config settings
        '''
        config = cherrypy.config.get('config')

        # catch checkboxes
        bools = filter(lambda s: not data.get(s),
            [
              'global.launchbrowser', 'global.updater',
              'XBMC.enabled', 'XBMC.onSnatch', 'XBMC.useWebAPIExistingCheck',
              'NMJ.enabled',
              'PLEX.enabled',
              'PROWL.enabled', 'PROWL.onSnatch',
              'GROWL.enabled', 'GROWL.onSnatch',
              'Notifo.enabled', 'Notifo.onSnatch',
              'Boxcar.enabled', 'Boxcar.onSnatch',
              'NMA.enable', 'NMA.onSnatch',
              'NMWP.enable', 'NMWP.onSnatch',
              'Twitter.enabled', 'Twitter.onSnatch',
              'Trakt.notification_enabled',
              'Trakt.watchlist_remove',
              'Trakt.watchlist_enabled',
              'Trakt.dontaddcollection',
              'Meta.enabled',
              'MovieETA.enabled',
              'Renamer.enabled', 'Renamer.trailerQuality', 'Renamer.cleanup',
              'Torrents.enabled',
              'NZB.enabled',
              'NZBMatrix.enabled', 'NZBMatrix.english', 'NZBMatrix.ssl',
              'NZBsRUS.enabled',
              'newzbin.enabled',
              'NZBsorg.enabled',
              'newznab.enabled',
              'x264.enabled',
              'Subtitles.enabled', 'Subtitles.addLanguage',
              'MovieRSS.enabled',
              'KinepolisRSS.enabled',
              'IMDBWatchlist.enabled',
            ]
        )
        data.update(data.fromkeys(bools, False))

        # Do quality order
        order = data.get('Quality.order').split(',')
        for id in order:
            qo = Db.query(QualityTemplate).filter_by(id = int(id)).one()
            qo.order = order.index(id)
            Db.flush()
        del data['Quality.order']

        # Save templates
        if data.get('Quality.templates'):
            templates = json.loads(data.get('Quality.templates'))
            Qualities().saveTemplates(templates)
        del data['Quality.templates']

        # Save post data
        for name in data:
            section = name.split('.')[0]
            var = name.split('.')[1]
            config.set(section, var, data[name])

        # Change cron interval
        self.cron.get('yarr').setInterval(config.get('Intervals', 'search'))

        config.save()

        self.flash.add('config', 'Settings successfully saved.')
        return redirect(cherrypy.request.headers.get('referer'))

    def testXBMC(self, **data):

        xbmc = XBMC()
        xbmc.test(data.get('XBMC.host'), data.get('XBMC.username'), data.get('XBMC.password'))

        return ''

    @cherrypy.expose
    def testNMJ(self, **data):

        nmj = NMJ()
        nmj.test(data.get('NMJ.host'), data.get('NMJ.database'), data.get('NMJ.mount'))

        return ''

    @cherrypy.expose
    def autoNMJ(self, **data):

        nmj = NMJ()
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        return nmj.auto(data.get('NMJ.host'))

    @cherrypy.expose
    def testPLEX(self, **data):

        plex = PLEX()
        plex.test(data.get('PLEX.host'))

        return ''

    @cherrypy.expose
    def testGROWL(self, **data):

        growl = GROWL()
        growl.test(data.get('GROWL.host'), data.get('GROWL.password'))

        return ''

    @cherrypy.expose
    def testPROWL(self, **data):

        prowl = PROWL()
        prowl.test(data.get('PROWL.keys'), data.get('PROWL.priority'))
        return ''

    @cherrypy.expose
    def testNotifo(self, **data):

        notifo = Notifo()
        notifo.test(data.get('Notifo.username'), data.get('Notifo.key'))

        return ''
    
    @cherrypy.expose
    def testBoxcar(self, **data):

        boxcar = Boxcar()
        boxcar.test(data.get('Boxcar.username'))

        return ''
    
    @cherrypy.expose
    def testNMA(self, **data):
        
        nma = NMA()
        nma.test(data.get('NMA.apikey'), data.get('NMA.devkey'), data.get('NMA.priority'))
        return ''

    @cherrypy.expose
    def testNMWP(self, **data):
        
        nmwp = NMWP()
        nmwp.test(data.get('NMWP.apikey'), data.get('NMWP.devkey'), data.get('NMWP.priority'))
        return ''
        
    @cherrypy.expose
    def testTwitter(self, **data):

        twitter = Twitter()
        twitter.test()
        return ''
    
    @cherrypy.expose
    def testTrakt(self, **data):

        trakt = Trakt()
        result = trakt.test(data.get('Trakt.apikey'), data.get('Trakt.username'), data.get('Trakt.password'))

        return str(result)

    @cherrypy.expose
    def twitterReqAuth(self):

        twitter = Twitter()
        referer = cherrypy.request.headers.get('referer')
        auth_url = twitter.get_authorization(referer)
        if not auth_url:
          return ('Error making an oauth connection to Twitter.  Check your '
                  'system time?  See the logs for a more detailed error.')
        return redirect(auth_url)

    @cherrypy.expose
    def twitterAuth(self, oauth_token=None, oauth_verifier=None, **params):

        twitter = Twitter()
        twitter.get_credentials(oauth_verifier)
        return redirect('../')

    @cherrypy.expose
    def exit(self):

        cherrypy.engine.exit()
        sys.exit()

    @cherrypy.expose
    def restart(self):

        cherrypy.engine.restart()

    @cherrypy.expose
    def update(self):

        updater = cherrypy.config.get('updater')
        result = updater.run()

        return 'Update successful, restarting...' if result else 'Update failed.'

    @cherrypy.expose
    def checkForUpdate(self):

        updater = cherrypy.config.get('updater')
        updater.checkForUpdate()

        return redirect(cherrypy.request.headers.get('referer'))

    @cherrypy.expose
    @cherrypy.tools.mako(filename = "config/userscript.js")
    def userscript(self, **data):
        '''
        imdb UserScript, for easy movie adding
        '''
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        return self.render({'host':data.get('host')})

