#!/usr/bin/env python
import sys
import os

rundir = os.path.dirname(os.path.abspath(__file__))
try:
    frozen = sys.frozen
except AttributeError:
    frozen = False

# Define path based on frozen state
if frozen:
    path_base = os.environ['_MEIPASS2']
    rundir = os.path.dirname(sys.executable)
    #path_base = os.path.dirname(sys.executable)
else:
    path_base = rundir

# Include paths
sys.path.insert(0, path_base)
sys.path.insert(0, os.path.join(path_base, 'library'))

# Configure logging
from app.config.cplog import CPLog
debug = os.path.isfile(os.path.join(path_base, 'debug.conf'))
log = CPLog()
log.config(os.path.join(rundir, 'logs'), debug)

# Create cache dir
cachedir = os.path.join(rundir, 'cache')
if not os.path.isdir(cachedir):
    os.mkdir(cachedir)

import cherrypy
import app.config.render
from app.config.db import initDb
from optparse import OptionParser
from app.config.configApp import configApp
from app.config.routes import setup as Routes
from app.lib.cron import CronJobs
from app.config.updater import Updater
from cherrypy.process import plugins

def server_start():
    p = OptionParser()
    p.add_option('-d', action = "store_true",
                 dest = 'daemonize', help = "Run the server as a daemon")
    p.add_option('-q', '--quiet', action = "store_true",
                 dest = 'quiet', help = "Don't log to console")
    p.add_option('-p', '--pidfile',
                 dest = 'pidfile', default = None,
                 help = "Store the process id in the given file")

    options, args = p.parse_args()

    config = os.path.join(rundir, 'config.ini')

    # Stop logging
    if options.quiet or options.daemonize:
        cherrypy.config.update({'log.screen': False})

    # Config app
    ca = configApp(config)
    initDb()

    # Start threads
    myCrons = CronJobs(cherrypy.engine, ca, debug)
    myCrons.subscribe()

    # Update script
    myUpdater = Updater(cherrypy.engine)
    myUpdater.subscribe()

    # User config, use own stuff to prevent unexpected results
    cherrypy.config.update({
        'global': {
            'server.thread_pool':               10,
            'server.socket_port':           int(ca.get('global', 'port')),
            'server.socket_host':               ca.get('global', 'host'),
            'server.environment':               ca.get('global', 'server.environment'),
            'engine.autoreload_on':             ca.get('global', 'server.environment') == 'development',
            'tools.mako.collection_size':       500,
            'tools.mako.directories':           os.path.join(path_base, 'app', 'views'),

            'basePath':                         path_base,
            'runPath':                          rundir,
            'cachePath':                        cachedir,
            'debug':                            debug,
            'frozen':                           frozen,

            # Global workers
            'config':                           ca,
            'updater':                          myUpdater,
            'cron':                             myCrons.threads,
            'searchers':                        myCrons.searchers,
            'flash':                            app.flash()
        }
    })

    # Static config
    conf = {
        '/': {
            'request.dispatch': Routes(),
            'tools.sessions.on':  True,
            'tools.sessions.timeout': 240,

            'tools.gzip.on': True,
            'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/css', 'text/javascript', 'application/javascript']
        },
        '/media':{
            'tools.staticdir.on': True,
            'tools.staticdir.root': path_base,
            'tools.staticdir.dir': "media",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
        },
        '/cache':{
            'tools.staticdir.on': True,
            'tools.staticdir.root': rundir,
            'tools.staticdir.dir': "cache",
            'tools.expires.on': True,
            'tools.expires.secs': 3600 * 24 * 7
        }
    }

    # Don't use auth when password is empty
    if ca.get('global', 'password') != '':
        conf['/'].update({
            'tools.basic_auth.on': True,
            'tools.basic_auth.realm': 'Awesomeness',
            'tools.basic_auth.users': {ca.get('global', 'username'):ca.get('global', 'password')},
            'tools.basic_auth.encrypt': app.clearAuthText
        })
        cherrypy.tools.mybasic_auth = cherrypy.Tool('on_start_resource', app.basicAuth)

    # I'll do my own logging, thanks!
    #cherrypy.log.error_log.propagate = False
    #cherrypy.log.access_log.propagate = False

    #No Root controller as we provided all our own.
    cherrypy.tree.mount(root = None, config = conf)

    #HTTP Errors
    def http_error_hander(status, message, traceback, version):
        args = [status, message, traceback, version]
        log.error("CherryPy caught an error: %s" % ", ".join(args))
        return "<html><body><h1>Error %s</h1>Something unexpected has happened. Please check the log.</body></html>" % args[0]
    cherrypy.config.update({'error_page.default' : http_error_hander})

    # Deamonize
    if options.daemonize:
        plugins.Daemonizer(cherrypy.engine).subscribe()

    # PIDfile
    if options.pidfile:
        plugins.PIDFile(cherrypy.engine, options.pidfile).subscribe()

    # Setup the signal handler
    if hasattr(cherrypy.engine, "signal_handler"):
        cherrypy.engine.signal_handler.subscribe()
    if hasattr(cherrypy.engine, "console_control_handler"):
        cherrypy.engine.console_control_handler.subscribe()


    ## start the app
    try:
        cherrypy.engine.start()
    except:
        sys.exit(1)
    else:

        # Launch browser
        if ca.get('global', 'launchbrowser'):
            app.launchBrowser(ca.get('global', 'host'), ca.get('global', 'port'))

        cherrypy.engine.block()


if __name__ == '__main__':
    server_start()
