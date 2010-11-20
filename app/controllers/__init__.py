from app.lib.qualities import Qualities
from library.minify import Minify
import cherrypy
import routes

def base():
    b = cherrypy.config.get('config').get('global', 'urlbase')
    if b:
        return '/' + b.strip('/')
    return ''

def url(*args, **kwargs):
    return cherrypy.url(routes.url_for(*args, **kwargs), base = base())

def redirect(url):
    b = base()
    if b:
        url = '/' + url.lstrip(b) if url else b
    else:
        url = url if url else b
    raise cherrypy.HTTPRedirect(url)

class BaseController:

    globals = {
        'url': url,
        'Qualities': Qualities(),
        'Minify': Minify()
    }

    def __init__(self):
        self.cron = cherrypy.config.get('cron')
        self.searchers = cherrypy.config.get('searchers')
        self.flash = self.globals['flash'] = cherrypy.config.get('flash')
        self.globals['debug'] = cherrypy.config.get('debug')
        self.globals['updater'] = cherrypy.config.get('updater')
        self.globals['searchers'] = self.searchers
        self.globals['cherrypy'] = cherrypy
        self.globals['config'] = cherrypy.config.get('config')

    def updateGlobals(self):

        self.globals['baseUrl'] = base() + '/'
        self.globals['yarr'] = self.cron.get('yarr')

    def render(self, list):

        self.updateGlobals()

        list.update(self.globals)

        return list
