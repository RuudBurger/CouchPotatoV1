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

def server_start():
    from optparse import OptionParser

    p = OptionParser()
    p.add_option('-d', action = "store_true",
                 dest = 'daemonize', help = "Run the server as a daemon")
    p.add_option('-q', '--quiet', action = "store_true",
                 dest = 'quiet', help = "Don't log to console")
    p.add_option('--nolaunch', action = "store_true",
                 dest = 'nolaunch', help="Don't start browser")
    p.add_option('-p', '--pidfile',
                 dest = 'pidfile', default = None,
                 help = "Store the process id in the given file")
    p.add_option('--config',
                 dest = 'config', default = None,
                 help = "Path to config.ini file")
    p.add_option('--datadir',
                 dest = 'datadir', default = None,
                 help = "Path to the data directory")
    p.add_option('--port',
                 dest = 'port', default = None,
                 help = "Force webinterface to listen on this port")


    options, args = p.parse_args()

    if options.datadir:
        datadir = options.datadir

        if not os.path.isdir(datadir):
            os.makedirs(datadir)

    else:
        datadir = rundir

    datadir = os.path.abspath(datadir)
    
    if not os.access(datadir, os.W_OK):
        raise SystemExit("Data dir must be writeable '" + datadir + "'")

    import app.config
    app.config.DATADIR = datadir

    if options.config:
        config = options.config
    else:
        config = os.path.join(datadir, 'config.ini')

    config = os.path.abspath(config)

    if not os.access(os.path.dirname(config), os.W_OK) and not os.access(config, os.W_OK):
        if not os.path.exists(os.path.dirname(config)):
            os.makedirs(os.path.dirname(config))
        else:
            raise SystemExit("Directory for config file must be writeable")

    import cherrypy
    import app.config.render

    # Configure logging
    from app.config.cplog import CPLog

    # Setup logging
    debug = os.path.isfile(os.path.join(datadir, 'debug.conf'))
    log = CPLog()
    log.config(os.path.join(datadir, 'logs'), debug)

    # Create cache dir
    cachedir = os.path.join(datadir, 'cache')
    if not os.path.isdir(cachedir):
        os.mkdir(cachedir)

    # Stop logging
    if options.quiet or options.daemonize:
        cherrypy.config.update({'log.screen': False})
    else:
        cherrypy.config.update({'log.screen': True})

    # Config app
    from app.config.configApp import configApp
    ca = configApp(config)

    # Setup db
    from app.config.db import initDb
    initDb()

    from app.config.routes import setup as Routes
    from app.lib.cron import CronJobs
    from app.config.updater import Updater
    from cherrypy.process import plugins

    # setup hostaddress
    if options.port:
        port = int(options.port)
    else:
        port = int(ca.get('global', 'port'))

    # Check an see if CP is already running
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = ca.get('global', 'host')
    try:
        s.connect((host, port))
        s.shutdown(0)
        if not options.nolaunch:
            app.launchBrowser(host, port)
        return
    except:
        pass

    # Start threads
    myCrons = CronJobs(cherrypy.engine, ca, debug)
    myCrons.subscribe()

    # Update script
    myUpdater = Updater(cherrypy.engine)
    myUpdater.subscribe()

    # User config, use own stuff to prevent unexpected results
    cherrypy.config.update({
        'global': {
            'server.thread_pool': 10,
            'server.socket_port': port,
            'server.socket_host': ca.get('global', 'host'),
            'server.environment': ca.get('global', 'server.environment'),
            'engine.autoreload_on': ca.get('global', 'server.environment') == 'development',
            'tools.mako.collection_size': 500,
            'tools.mako.directories': os.path.join(path_base, 'app', 'views'),

            'basePath': path_base,
            'runPath': rundir,
            'cachePath': cachedir,
            'debug': debug,
            'frozen': frozen,

            # Global workers
            'config': ca,
            'updater': myUpdater,
            'cron': myCrons.threads,
            'searchers': myCrons.searchers,
            'flash': app.flash()
        }
    })

    # Static config
    conf = {
        '/': {
            'request.dispatch': Routes(),
            'tools.sessions.on': True,
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
            'tools.staticdir.root': datadir,
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
        return "<html><body><h1>Error %s</h1>Something unexpected has happened.</body></html>" % args[0]
    cherrypy.config.update({'error_page.default' : http_error_hander})

    # Deamonize
    if options.daemonize:
        plugins.Daemonizer(cherrypy.engine).subscribe()

    # PIDfile
    if options.pidfile:
        plugins.PIDFile(cherrypy.engine, options.pidfile).subscribe()

    # Setup the signal handler
    if hasattr(cherrypy.engine, "signal_handler"):
        if not options.quiet and not options.daemonize:
           cherrypy.engine.signal_handler.set_handler(signal='SIGINT', listener=cherrypy.engine.signal_handler.bus.exit)
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
        if not options.nolaunch:
            if ca.get('global', 'launchbrowser'):
                app.launchBrowser(ca.get('global', 'host'), port)

        cherrypy.engine.block()


if __name__ == '__main__':
    server_start()

