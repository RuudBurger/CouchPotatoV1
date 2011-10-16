from app import latinToAscii
from app.config.cplog import CPLog
from app.config.db import Movie, Session as Db, MovieQueue
from app.lib import hashFile
from app.lib.qualities import Qualities
import cherrypy
import fnmatch
import json
import os
import re
import subprocess

log = CPLog(__name__)

class Library:

    def __init__(self):
        self.config = cherrypy.config.get('config')

    minimalFileSize = 1024 * 1024 * 200 # 10MB
    ignoredInPath = ['extracted', '_unpack', '_failed_', '_unknown_', '_exists_', '.appledouble', '.appledb', '.appledesktop', '/._', 'cp.cpnfo'] #unpacking, smb-crap, hidden files
    ignoreNames = ['extract', 'extracting', 'extracted', 'movie', 'movies', 'film', 'films']
    extensions = {
        'movie': ['*.mkv', '*.wmv', '*.avi', '*.mpg', '*.mpeg', '*.mp4', '*.m4v', '*.m2ts', '*.iso', '*.img', '*.vob'],
        'nfo': ['*.nfo'],
        'subtitle': ['*.sub', '*.srt', '*.ssa', '*.ass'],
        'subtitleExtras': ['*.idx'],
        'trailer': ['*.mov', '*.mp4', '*.flv'],
        'cpnfo': ['cp.cpnfo']
    }
    codecs = {
        'audio': ['dts', 'ac3', 'ac3d', 'mp3'],
        'video': ['x264', 'divx', 'xvid']
    }

    sourceMedia = {
        'bluray': ['bluray', 'blu-ray', 'brrip', 'br-rip'],
        'hddvd': ['hddvd', 'hd-dvd'],
        'dvd': ['dvd'],
        'hdtv': ['hdtv']
    }

    # From Plex/XBMC
    clean = '(?i)[^\s](ac3|dts|custom|dc|divx|divx5|dsr|dsrip|dutch|dvd|dvdrip|dvdscr|dvdscreener|screener|dvdivx|cam|fragment|fs|hdtv|hdrip|hdtvrip|internal|limited|multisubs|ntsc|ogg|ogm|pal|pdtv|proper|repack|rerip|retail|r3|r5|bd5|se|svcd|swedish|german|read.nfo|nfofix|unrated|ws|telesync|ts|telecine|tc|brrip|bdrip|480p|480i|576p|576i|720p|720i|1080p|1080i|hrhd|hrhdtv|hddvd|bluray|x264|h264|xvid|xvidvd|xxx|www.www|cd[1-9]|\[.*\])[^\s]*'
    multipartRegEx = [
        '[ _\.-]+cd[ _\.-]*([0-9a-d]+)', #*cd1
        '[ _\.-]+dvd[ _\.-]*([0-9a-d]+)', #*dvd1
        '[ _\.-]+part[ _\.-]*([0-9a-d]+)', #*part1.mkv
        '[ _\.-]+dis[ck][ _\.-]*([0-9a-d]+)', #*disk1.mkv
        '()[ _\.-]+([0-9]*[abcd]+)(\.....?)$',
        '([a-z])([0-9]+)(\.....?)$',
        '()([ab])(\.....?)$' #*a.mkv 
    ]
    noTables = False

    def getMovies(self, folder = None, withMeta = True):
        log.debug('getMoviesStart')

        movies = []
        qualities = Qualities()

        movieFolder = unicode(folder) if folder else self.config.get('Renamer', 'destination')
        if not os.path.isdir(movieFolder):
            log.error('Can\'t find directory: %s' % movieFolder)
            return movies

        log.debug('os.walk(movieFolder) %s' % movieFolder)
        # Walk the tree once to catch any UnicodeDecodeErrors that might arise
        # from malformed file and directory names. Use the non-unicode version
        # of movieFolder if so.
        try:
            for x in os.walk(movieFolder): pass
            walker = os.walk(movieFolder)
        except UnicodeDecodeError:
            walker = os.walk(str(movieFolder))
        for root, subfiles, filenames in walker:
            if self.abort:
                log.debug('Aborting moviescan')
                return movies

            movie = {
                'movie': None,
                'queue': 0,
                'match': False,
                'meta': {},
                'info': {
                    'name': None,
                    'cpnfoImdb': None,
                    'ppScriptName': None,
                    'imdb': None,
                    'year': None,
                    'quality': '',
                    'resolution': None,
                    'sourcemedia': '',
                    'size': 0,
                    'codec': {
                        'video': '',
                        'audio': ''
                    },
                    'group': ''
                },
                'history': None,
                'path': root,
                'folder': root.split(os.path.sep)[-1:].pop(),
                'nfo':[], 'files':[], 'trailer':[], 'cpnfo':None,
                'subtitles':{
                    'files': [],
                    'extras': []
                }
            }

            if movie['folder'] == 'VIDEO_TS':
                movie['folder'] = movie['path'].split(os.path.sep)[-2:-1].pop()

            patterns = []
            for extType in self.extensions.itervalues():
                patterns.extend(extType)

            for pattern in patterns:
                for filename in fnmatch.filter(sorted(filenames), pattern):
                    fullFilePath = os.path.join(root, filename)
                    log.debug('Processing file: %s' % fullFilePath)

                    new = {
                       'filename': filename,
                       'ext': os.path.splitext(filename)[1].lower()[1:], #[1:]to remove . from extension
                    }

                    #cpnfo
                    if new.get('filename') in self.extensions['cpnfo']:
                        movie['cpnfo'] = new.get('filename')
                    #nfo file
                    if('*.' + new.get('ext') in self.extensions['nfo']):
                        movie['nfo'].append(filename)
                    #subtitle file
                    elif('*.' + new.get('ext') in self.extensions['subtitle']):
                        movie['subtitles']['files'].append(new)
                    #idx files
                    elif('*.' + new.get('ext') in self.extensions['subtitleExtras']):
                        movie['subtitles']['extras'].append(new)
                    #trailer file
                    elif re.search('(^|[\W_])trailer\d*[\W_]', filename.lower()) and self.filesizeBetween(fullFilePath, 2, 250):
                        movie['trailer'].append(new)
                    else:
                        #ignore movies files / or not
                        if self.keepFile(fullFilePath):
                            log.debug('self.keepFile(fullFilePath)')
                            new['hash'] = hashFile(fullFilePath) # Add movie hash
                            new['size'] = os.path.getsize(fullFilePath) # File size
                            movie['files'].append(new)

            if movie['files']:
                log.debug('Files found')
                #Find movie by cpnfo
                if movie['cpnfo']:
                    log.debug('Scanning cpnfo')
                    cpnfoFile = open(os.path.join(movie['path'], movie['cpnfo']), 'r').readlines()
                    cpnfoFile = [x.strip() for x in cpnfoFile]
                    movie['info']['ppScriptName'] = cpnfoFile[0]
                    movie['info']['cpnfoImdb'] = cpnfoFile[1]

                # Find movie by nfo
                if movie['nfo']:
                    log.debug('Scanning nfo')
                    for nfo in movie['nfo']:
                        nfoFile = open(os.path.join(movie['path'], nfo), 'r').read()
                        movie['info']['imdb'] = self.getImdb(nfoFile)

                # Find movie via files
                log.debug('self.determineMovie(movie)')
                movie['movie'] = self.determineMovie(movie)

                if movie['movie']:
                    movie['match'] = True

                    log.debug('self.getHistory(movie[movie])')
                    movie['history'] = self.getHistory(movie['movie'])
                    movie['queue'] = self.getQueue(movie['movie'])

                    movie['info']['name'] = movie['movie'].name
                    movie['info']['year'] = movie['movie'].year
                    try:
                        movie['info']['quality'] = qualities.types.get(movie['queue'].qualityType).get('label')
                    except:
                        movie['info']['quality'] = qualities.guess([os.path.join(movie['path'], file['filename']) for file in movie['files']])

                    for file in movie['files']:
                        movie['info']['size'] += file['size']

                    movie['info']['size'] = str(movie['info']['size'])
                    movie['info']['group'] = self.getGroup(movie['folder'])
                    movie['info']['codec']['video'] = self.getCodec(movie['folder'], self.codecs['video'])
                    movie['info']['codec']['audio'] = self.getCodec(movie['folder'], self.codecs['audio'])

                    #get metainfo about file
                    if withMeta:
                        log.debug('self.getHistory(movie[movie])')
                        testFile = os.path.join(movie['path'], movie['files'][0]['filename'])
                        try:
                            movie['meta'].update(self.getMeta(testFile))
                        except:
                            pass

                        #check the video file for its resolution
                        if movie['meta'].has_key('video stream'):
                            width = movie['meta']['video stream'][0]['image width']
                            height = movie['meta']['video stream'][0]['image height']

                            if width and height:
                                if width > 1900 and width < 2000 and height <= 1080:
                                    namedResolution = '1080p'
                                elif width > 1200 and width < 1300 and height <= 720:
                                    namedResolution = '720p'
                                else:
                                    namedResolution = None
                        else:
                            log.info("Unable to fetch audio/video details for %s" % testFile)
                            namedResolution = None

                        movie['info']['resolution'] = namedResolution
                        movie['info']['sourcemedia'] = self.getSourceMedia(testFile)

                # Create filename without cd1/cd2 etc
                log.debug('removeMultipart')
                movie['filename'] = self.removeMultipart(os.path.splitext(movie['files'][0]['filename'])[0])

                # Give back ids, not table rows
                if self.noTables:
                    log.debug('self.noTables')
                    movie['history'] = [h.id for h in movie['history']] if movie['history'] else movie['history']
                    movie['movie'] = movie['movie'].id if movie['movie'] else movie['movie']

                log.debug('movies.append(movie)')
                movies.append(movie)

        log.debug('getMoviesEnd')
        return movies

    def removeMultipart(self, name):
        for regex in self.multipartRegEx:
            try:
                found = re.sub(regex, '', name)
                if found != name:
                    return found
            except:
                pass
        return name

    def getHistory(self, movie):
        if movie.queue:
            for queue in movie.queue:
                if queue.renamehistory and queue.renamehistory[0]:
                    return queue.renamehistory

        return None

    def getQueue(self, movie):
        try:
            for queue in movie.queue:
                if queue.name:
                    return queue
        except TypeError:
            return None

        return None

    def determineMovie(self, movie):
        result = False

        movieName = self.cleanName(movie['folder'])
        movieYear = self.findYear(movie['folder'])

        #check to see if the downloaded movie nfo file agrees with what we thought we were downloading
        if movie['info']['cpnfoImdb'] and movie['info']['imdb']:
            cpnfoimdb = 'tt' + movie['info']['cpnfoImdb'].replace("tt", '')
            nfoimdb = 'tt' + movie['info']['imdb'].replace("tt", '')
            if cpnfoimdb != nfoimdb:
                log.info("Downloaded movie's nfo has imdb id that doesn't match what we though we downloaded")
            movie['info']['imdb'] = cpnfoimdb

        if movie['info']['imdb']:
            byImdb = self.getMovieByIMDB(movie['info']['imdb'])
            if byImdb:
                return byImdb
            else:
                result = cherrypy.config['searchers']['movie'].findByImdbId(movie['info']['imdb'])

        if not result:

            # Check and see if name is in queue
            try:
                queue = Db.query(MovieQueue).filter_by(name = movie['folder']).first()
                if queue:
                    log.info('Found movie via MovieQueue.')
                    return queue.Movie
            except:
                pass

            # Find movie via movie name
            try:
                m = Db.query(Movie).filter_by(name = movieName).first()
                if m:
                    log.info('Found movie via moviename.')
                    return m
            except:
                pass

            # Try and match the movies via filenaming
            for file in movie['files']:
                dirnames = movie['path'].lower().replace(unicode(self.config.get('Renamer', 'download')).lower(), '').split(os.path.sep)
                dirnames.append(file['filename'])
                dirnames.reverse()

                for dir in dirnames:
                    dir = self.cleanName(dir)

                    # last resort, match every word in path to db
                    lastResort = {}
                    dirSplit = re.split('\W+', dir.lower())
                    for s in dirSplit:
                        if s:
                            results = Db.query(Movie).filter(Movie.name.like('%' + s + '%')).filter_by(year = movieYear).all()
                            for r in results:
                                lastResort[r.id] = r

                    for l in lastResort.itervalues():
                        wordCount = 0
                        for word in dirSplit:
                            if word in l.name.lower():
                                wordCount += 1

                        if wordCount == len(dirSplit) and len(dirSplit) > 0:
                            return l

            # Search tMDB
            if movieName and not movieName in ['movie']:
                log.info('Searching for "%s".' % movie['folder'])
                result = cherrypy.config['searchers']['movie'].find(movieName + ' ' + movieYear, limit = 1)

        if result:
            movie = self.getMovieByIMDB(result.imdb)

            if not movie:
                new = Movie()
                Db.add(new)

                try:
                    # Add found movie as downloaded
                    new.status = u'downloaded'
                    new.name = result.name
                    new.imdb = result.imdb
                    new.movieDb = result.id
                    new.year = result.year
                    Db.flush()

                    return new
                except Exception, e:
                    log.error('Movie could not be added to database %s. %s' % (result, e))
            else:
                return movie

        return None

    def cleanName(self, text):
        cleaned = ' '.join(re.split('\W+', latinToAscii(text).lower()))
        cleaned = re.sub(self.clean, ' ', cleaned)
        year = self.findYear(cleaned)

        if year: # Split name on year
            try:
                movieName = cleaned.split(year).pop(0).strip()
                return movieName
            except:
                pass
        else: # Split name on multiple spaces
            try:
                movieName = cleaned.split('  ').pop(0).strip()
                return movieName
            except:
                pass

        return None

    def findYear(self, text):
        matches = re.search('(?P<year>[0-9]{4})', text)
        if matches:
            return matches.group('year')

        return ''

    def getImdb(self, txt):
        try:
            m = re.search('(?P<id>tt[0-9{7}]+)', txt)
            id = m.group('id')
            if id:
                return id
        except AttributeError:
            return False

        return False

    def getMovieByIMDB(self, imdbId):
        '''
        Get movie based on IMDB id.
        If not in local DB, go fetch it from theMovieDb
        '''
        m = Db.query(Movie).filter_by(imdb = imdbId).first()
        if m:
            return m

    def getCodec(self, filename, codecs):
        codecs = map(re.escape, codecs)
        try:
            codec = re.search('[^A-Z0-9](?P<codec>' + '|'.join(codecs) + ')[^A-Z0-9]', filename, re.I)
            return (codec and codec.group('codec')) or ''
        except:
            return ''

    def getGroup(self, filename):
        try:
            group = re.search('-(?P<group>[A-Z0-9]+)$', filename, re.I)
            if group != None:
                groupname = group.group('group')
            else:
		# In case there is no "-" seperator, it means it seperated by spaces. so i'll use last word sperated by " ".
                groupname = filename.split(" ")[-1]

            log.info("%s's group name is %s" % (filename, groupname))
            return groupname
        except:
            return ''

    def getSourceMedia(self, file):
        '''
        get source media from filename... durr
        '''

        #TODO: handle filenames that have multiple source medias in them
        medias = []
        for media in self.sourceMedia:
            for mediaAlias in self.sourceMedia[media]:
                if mediaAlias in file.lower():
                    medias.append(media)

        try:
            return medias[0]
        except:
            return None

    def getMeta(self, filename):
        '''
        A hacky way to keep hachoir from locking the file so that we can actually move it after
        getting metadata.  This is temporary.

        Writes temp_file_contents, b64decoded, to a temp python file and runs that file as a subprocess to get the
        file resolution.
        '''

        libraryDir = os.path.join(cherrypy.config.get('basePath'), 'library')
        script = os.path.join(libraryDir, 'getmeta.py')

        # Use the current python interpreter, if possible. Cannot rely on just using "python" because on some
        # system (ie. ArchLinux), the default "python" interpreter is python 3, and that will not work here.
        pyinterp = sys.executable
        if not pyinterp: pyinterp = "python"

        p = subprocess.Popen([pyinterp, script, filename], stdout = subprocess.PIPE, stderr = subprocess.PIPE, cwd = libraryDir)
        z = p.communicate()[0]

        try:
            meta = json.loads(z)
            log.info('Retrieved metainfo: %s' % meta)
            return meta
        except:
            log.error('Couldn\'t get metadata from file')

    def filesizeBetween(self, file, min = 0, max = 100000):
        try:
            return (min * 1048576) < os.path.getsize(file) < (max * 1048576)
        except:
            log.error('Couldn\'t get filesize of %s.' % file)

        return False

    def keepFile(self, file):

        # ignoredpaths
        for i in self.ignoredInPath:
            if i in file.lower():
                log.debug('Path contains " %s ".' % i)
                return False

        # Sample file
        if re.search('(^|[\W_])sample\d*[\W_]', file.lower()):
            return False

        # Minimal size
        if self.filesizeBetween(file, self.minimalFileSize):
            log.info('File to small: %s' % file)
            return False

        # All is OK
        return True
