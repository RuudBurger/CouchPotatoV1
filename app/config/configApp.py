from app.config.cplog import CPLog
import ConfigParser

log = CPLog(__name__)

class configApp():

    s = ['Sabnzbd', 'TheMovieDB', 'NZBsorg', 'Renamer', 'IMDB', 'Intervals']
    bool = {'true':True, 'false':False}

    def __init__(self, file):
        self.file = file

        self.p = ConfigParser.RawConfigParser()
        self.p.read(file)

        self.initConfig()

    def parser(self):
        return self.p

    def sections(self):
        return self.s

    def set(self, section, option, value):
        return self.p.set(section, option, value)

    def get(self, section, option):
        value = self.p.get(section, option)
        if str(value).lower() in self.bool:
            return self.bool.get(str(value).lower())
        return value if type(value) != str else value.strip()

    def initConfig(self):
        '''
        Create sections, in case the make-config didnt work properly
        '''

        self.addSection('global')
        self.setDefault('global', 'server.environment', 'production')
        self.setDefault('global', 'host', '0.0.0.0')
        self.setDefault('global', 'port', 5000)
        self.setDefault('global', 'username', '')
        self.setDefault('global', 'password', '')
        self.setDefault('global', 'launchbrowser', True)
        self.setDefault('global', 'updater', True)
        self.setDefault('global', 'git', 'git')
        self.setDefault('global', 'urlBase', '')
        self.setDefault('global', 'ignoreWords', '')
        self.setDefault('global', 'preferredWords', '')
        self.setDefault('global', 'requiredWords', '')

        self.addSection('Renamer')
        self.setDefault('Renamer', 'enabled', False)
        self.setDefault('Renamer', 'download', '')
        self.setDefault('Renamer', 'destination', '')
        self.setDefault('Renamer', 'folderNaming', '<namethe> (<year>)')
        self.setDefault('Renamer', 'fileNaming', '<thename><cd>.<ext>')
        self.setDefault('Renamer', 'separator', ' ')
        self.setDefault('Renamer', 'cleanup', False)

        self.addSection('Trailer')
        self.setDefault('Trailer', 'quality', False)
        self.setDefault('Trailer', 'name', 'movie-trailer')

        self.addSection('NZBsorg')
        self.setDefault('NZBsorg', 'enabled', True)
        self.setDefault('NZBsorg', 'id', '')
        self.setDefault('NZBsorg', 'key', '')
        self.addSection('NZBMatrix')
        self.setDefault('NZBMatrix', 'enabled', True)
        self.setDefault('NZBMatrix', 'username', '')
        self.setDefault('NZBMatrix', 'apikey', '')
        self.setDefault('NZBMatrix', 'english', False)
        self.addSection('newzbin')
        self.setDefault('newzbin', 'enabled', False)
        self.setDefault('newzbin', 'username', '')
        self.setDefault('newzbin', 'password', '')
        self.addSection('newznab')
        self.setDefault('newznab', 'enabled', False)
        self.setDefault('newznab', 'host', '')
        self.setDefault('newznab', 'apikey', '')
        self.addSection('NZBsRUS')
        self.setDefault('NZBsRUS', 'enabled', False)
        self.setDefault('NZBsRUS', 'userid', '')
        self.setDefault('NZBsRUS', 'userhash', '')
        self.addSection('x264')
        self.setDefault('x264', 'enabled', False)
        self.addSection('mysterbin')
        self.setDefault('mysterbin', 'enabled', False)

        self.addSection('NZB')
        self.setDefault('NZB', 'enabled', True)
        self.setDefault('NZB', 'retention', 300)
        self.setDefault('NZB', 'sendTo', 'Sabnzbd')
        self.setDefault('NZB', 'blackhole', '')

        self.addSection('Torrents')
        self.setDefault('Torrents', 'enabled', False)
        self.setDefault('Torrents', 'wait', 24)
        self.setDefault('Torrents', 'sendTo', 'Blackhole')
        self.setDefault('Torrents', 'blackhole', '')

        self.addSection('Sabnzbd')
        self.setDefault('Sabnzbd', 'host', 'localhost:8080')
        self.setDefault('Sabnzbd', 'apikey', '')
        self.setDefault('Sabnzbd', 'username', '')
        self.setDefault('Sabnzbd', 'password', '')
        self.setDefault('Sabnzbd', 'category', '')
        self.setDefault('Sabnzbd', 'ppDir', '')

        self.addSection('Transmission')
        self.setDefault('Transmission', 'host', 'localhost:9091')
        self.setDefault('Transmission', 'username', '')
        self.setDefault('Transmission', 'password', '')
        self.setDefault('Transmission', 'paused', '')
        self.setDefault('Transmission', 'directory', '')
        self.setDefault('Transmission', 'ratio', '')

        self.addSection('Nzbget')
        self.setDefault('Nzbget', 'host', '')
        self.setDefault('Nzbget', 'password', 'tegbzn6789')
        self.setDefault('Nzbget', 'category', 'Movies')

        self.addSection('TheMovieDB')
        self.setDefault('TheMovieDB', 'key', '9b939aee0aaafc12a65bf448e4af9543')

        self.addSection('RottenTomatoes')
        self.setDefault('RottenTomatoes', 'key', 'ht6hjvs5ez52am3tar58qxah')

        self.addSection('IMDB')

        self.addSection('Intervals')
        self.setDefault('Intervals', 'search', '24')
        self.setDefault('Intervals', 'renamer', '5')

        self.addSection('Quality')
        self.setDefault('Quality', 'hide', 'cam')
        self.setDefault('Quality', 'default', '720p')

        from app.lib.qualities import Qualities
        for type in Qualities.types.itervalues():
            self.setDefault('Quality', 'sMin-' + type['key'], type['size'][0])
            self.setDefault('Quality', 'sMax-' + type['key'], type['size'][1])

        self.addSection('Subtitles')
        self.setDefault('Subtitles', 'enabled', False)
        self.setDefault('Subtitles', 'languages', 'en')
        self.setDefault('Subtitles', 'addLanguage', True)
        self.setDefault('Subtitles', 'name', 'filename') #filename, subtitle

        self.addSection('MovieETA')
        self.setDefault('MovieETA', 'enabled', True)

        self.addSection('MovieRSS')
        self.setDefault('MovieRSS', 'enabled', False)
        self.setDefault('MovieRSS', 'minyear', '2000')
        self.setDefault('MovieRSS', 'minrating', '6.0')
        self.setDefault('MovieRSS', 'minvotes', '900')

        self.addSection('KinepolisRSS')
        self.setDefault('KinepolisRSS', 'enabled', False)
        self.setDefault('KinepolisRSS', 'minyear', '2000')
        self.setDefault('KinepolisRSS', 'minrating', '6.0')
        self.setDefault('KinepolisRSS', 'minvotes', '900')

        self.addSection('Trakt')
        self.setDefault('Trakt', 'watchlist_enabled', False)
        self.setDefault('Trakt', 'notification_enabled', False)
        self.setDefault('Trakt', 'watchlist_remove', False)
        self.setDefault('Trakt', 'dontaddcollection', True)
        self.setDefault('Trakt', 'apikey', '')
        self.setDefault('Trakt', 'username', '')
        self.setDefault('Trakt', 'password', '')

        self.addSection('XBMC')
        self.setDefault('XBMC', 'enabled', False)
        self.setDefault('XBMC', 'onSnatch', False)
        self.setDefault('XBMC', 'host', 'localhost')
        self.setDefault('XBMC', 'username', 'xbmc')
        self.setDefault('XBMC', 'password', 'xbmc')
        self.setDefault('XBMC', 'dbpath', '')
        self.setDefault('XBMC', 'updateOneOnly', False)
        self.setDefault('XBMC', 'useWebAPIExistingCheck', False)

        self.addSection('NMJ')
        self.setDefault('NMJ', 'enabled', False)
        self.setDefault('NMJ', 'host', '')
        self.setDefault('NMJ', 'database', '')
        self.setDefault('NMJ', 'mount', '')

        self.addSection('PLEX')
        self.setDefault('PLEX', 'enabled', False)
        self.setDefault('PLEX', 'host', '')

        self.addSection('PROWL')
        self.setDefault('PROWL', 'enabled', False)
        self.setDefault('PROWL', 'onSnatch', False)
        self.setDefault('PROWL', 'keys', '')
        self.setDefault('PROWL', 'priority', '0')

        self.addSection('GROWL')
        self.setDefault('GROWL', 'enabled', False)
        self.setDefault('GROWL', 'onSnatch', False)
        self.setDefault('GROWL', 'host', 'localhost')
        self.setDefault('GROWL', 'password', '')

        self.addSection('Notifo')
        self.setDefault('Notifo', 'enabled', False)
        self.setDefault('Notifo', 'onSnatch', False)
        self.setDefault('Notifo', 'username', '')
        self.setDefault('Notifo', 'key', '')

        self.addSection('Boxcar')
        self.setDefault('Boxcar', 'enabled', False)
        self.setDefault('Boxcar', 'onSnatch', False)
        self.setDefault('Boxcar', 'username', '')

        self.addSection('NMA')
        self.setDefault('NMA', 'enabled', False)
        self.setDefault('NMA', 'onSnatch', False)
        self.setDefault('NMA', 'apikey', '')
        self.setDefault('NMA', 'devkey', '')
        self.setDefault('NMA', 'priority', '0')

        self.addSection('Twitter')
        self.setDefault('Twitter', 'enabled', False)
        self.setDefault('Twitter', 'onSnatch', False)
        self.setDefault('Twitter', 'username', '')
        self.setDefault('Twitter', 'password', '')
        self.setDefault('Twitter', 'isAuthenticated', False)

        self.addSection('Synoindex')
        self.setDefault('Synoindex', 'enabled', False)

        self.addSection('Meta')
        self.setDefault('Meta', 'enabled', False)
        self.setDefault('Meta', 'urlOnly', False)
        self.setDefault('Meta', 'fanartMinHeight', 0)
        self.setDefault('Meta', 'fanartMinWidth', 0)
        self.setDefault('Meta', 'posterMinHeight', 0)
        self.setDefault('Meta', 'posterMinWidth', 0)
        self.setDefault('Meta', 'fanartFileName', 'fanart.<orig_ext>')
        self.setDefault('Meta', 'posterFileName', 'movie.tbn')
        self.setDefault('Meta', 'nfoFileName', 'movie.nfo')

        self.save()

    def save(self):
        with open(self.file, 'wb') as configfile:
            self.p.write(configfile)

    def addSection(self, section):
        if not self.p.has_section(section):
            self.p.add_section(section)

    def setDefault(self, section, option, value):
        if not self.p.has_option(section, option):
            self.p.set(section, option, value)

class Auth():

    def __init__(self, username, password):
        self.u = username
        self.p = password

    def test(self, environ, username, password):
        if username == self.u and password == self.p:
            return True
        else:
            return False
