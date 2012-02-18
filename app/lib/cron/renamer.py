from app import latinToAscii
from app.config.cplog import CPLog
from app.config.db import RenameHistory, Session as Db
from app.lib import xbmc
from app.lib import nmj
from app.lib import plex
from app.lib import prowl
from app.lib import growl
from app.lib import notifo
from app.lib import boxcar
from app.lib.cron.base import cronBase
from app.lib.library import Library
from app.lib.xbmc import XBMC
from app.lib.nmj import NMJ
from app.lib.plex import PLEX
from app.lib.prowl import PROWL
from app.lib.growl import GROWL
from app.lib.notifo import Notifo
from app.lib.boxcar import Boxcar
from app.lib.nma import NMA
from app.lib.twitter import Twitter
from app.lib.synoindex import Synoindex
from app.lib.trakt import Trakt
from xmg import xmg
import cherrypy
import os
import re
import shutil
import time
import traceback
import subprocess

log = CPLog(__name__)

class RenamerCron(cronBase, Library):

    ''' Cronjob for renaming movies '''

    lastChecked = 0
    intervalSec = 60
    config = {}

    def conf(self, option):
        return self.config.get('Renamer', option)

    def run(self):
        log.info('Renamer thread is running.')

        if not os.path.isdir(self.conf('download')):
            log.info("Watched folder doesn't exist.")

        wait = 0.1 if self.debug else 5

        time.sleep(10)
        while True and not self.abort:
            now = time.time()
            if (self.lastChecked + self.intervalSec) < now:
                try:
                    self.running = True
                    self.lastChecked = now
                    self.doRename()
                    self.running = False
                except Exception as exc:
                    log.error("!!Uncought exception in renamer thread.")
                    log.error(traceback.format_exc())
            time.sleep(wait)

        log.info('Renamer has shutdown.')

    def isDisabled(self):

        if (self.conf('enabled') and os.path.isdir(self.conf('download')) and self.conf('download') and self.conf('destination') and self.conf('foldernaming') and self.conf('filenaming')):
            download = self.conf('download')
            destination = self.conf('destination')
            if destination == download or download in destination:
                log.error("Download folder and movie destination shouldn't be the same. Change it in Settings >> Renaming.")
                return True
            return False
        else:
            return True

    def doRename(self):
        '''
        Go find files and rename them!
        '''

        log.debug('Starting renaming')

        if self.isDisabled():
            log.debug('Renaming is disabled')
            return

        allMovies = self.getMovies(self.conf('download'))
        log.debug('Movies: %s' % allMovies)

        if allMovies:
            log.debug("Ready to rename some files.")
        
        for movie in allMovies:
            if movie.get('match'):
                log.debug('self.renameFiles(movie)')
                finalDestination = self.renameFiles(movie)
                
                # Search for trailer & subtitles
                log.debug('crons')
                cherrypy.config['cron']['trailer'].forDirectory(finalDestination['directory'])
                cherrypy.config['cron']['subtitle'].forDirectory(finalDestination['directory'])

                # Update Metadata
                if self.config.get('Meta', 'enabled'):
                    log.debug('metadata')
                    nfoFileName = self.config.get('Meta', 'nfoFileName')
                    fanartFileNaming = self.config.get('Meta', 'fanartFileName')
                    fanartMinHeight = self.config.get('Meta', 'fanartMinHeight')
                    fanartMinWidth = self.config.get('Meta', 'fanartMinWidth')
                    posterFileNaming = self.config.get('Meta', 'posterFileName')
                    posterMinHeight = self.config.get('Meta', 'posterMinHeight')
                    posterMinWidth = self.config.get('Meta', 'posterMinWidth')

                    try:
                        x = xmg.MetaGen(movie['movie'].imdb)
                        fanartOrigExt = os.path.splitext(x.get_fanart_url(fanartMinHeight, fanartMinWidth))[-1][1:]
                        posterOrigExt = os.path.splitext(x.get_poster_url(posterMinHeight, posterMinWidth))[-1][1:]

                        nfo_location = os.path.join(finalDestination['directory'],
                                                    self.genMetaFileName(movie, nfoFileName))
                        fanart_filename = self.genMetaFileName(movie,
                                                               fanartFileNaming,
                                                               add_tags = {'orig_ext': fanartOrigExt})
                        poster_filename = self.genMetaFileName(movie,
                                                               posterFileNaming,
                                                               add_tags = {'orig_ext': posterOrigExt})

                        urlOnly = self.config.get('Meta', 'urlOnly')
                        x.write_nfo(nfo_location, url = True, xml = False)

                        x.write_fanart(fanart_filename,
                                       finalDestination['directory'],
                                       fanartMinHeight,
                                       fanartMinWidth)

                        x.write_poster(poster_filename,
                                       finalDestination['directory'],
                                       posterMinHeight,
                                       posterMinWidth)

                        log.info('XBMC metainfo for imdbid, %s, generated' % movie['movie'].imdb)
                    except Exception, e:
                        log.error('XMG TMDB API failure.  Please report to developers. API returned: %s' % e)
                        log.error(traceback.format_exc())
                
                # Run post-processing Scripts
                self._run_extra_script(finalDestination)
                
                # Notify XBMC
                log.debug('XBMC')
                xbmc = XBMC()
                xbmc.notify('Downloaded %s (%s)' % (movie['movie'].name, movie['movie'].year))
                xbmc.updateLibrary()

                # Notify NMJ
                log.debug('NMJ')
                nmj = NMJ()
                nmj.updateLibrary()

                # Notify PLEX
                log.debug('PLEX')
                plex = PLEX()
                plex.updateLibrary()

                # Notify PROWL
                log.debug('PROWL')
                prowl = PROWL()
                prowl.notify('Downloaded %s (%s)' % (movie['movie'].name, movie['movie'].year), 'Download Complete')

                # Notify GROWL
                log.debug('GROWL')
                growl = GROWL()
                growl.notify('Downloaded %s (%s)' % (movie['movie'].name, movie['movie'].year), 'Download Complete')

                # Notify Notifo
                log.debug('Notifo')
                notifo = Notifo()
                notifo.notify('%s (%s)' % (movie['movie'].name, movie['movie'].year), "Downloaded:")

                # Notify Boxcar
                log.debug('Boxcar')
                boxcar = Boxcar()
                boxcar.notify('%s (%s)' % (movie['movie'].name, movie['movie'].year), "Downloaded:")

                #Notify NotifyMyAndroid
                log.debug('NotifyMyAndroid')
                nma = NMA()
                nma.notify('Download Complete', 'Downloaded %s (%s)' % (movie['movie'].name, movie['movie'].year))

                # Notify Twitter
                log.debug('Twitter')
                twitter = Twitter()
                twitter.notify('Download Finished', 'Downloaded %s (%s)' % (movie['movie'].name, movie['movie'].year))

                # Notify Synoindex
                log.debug('Synoindex')
                synoindex = Synoindex()
                synoindex.addToLibrary(finalDestination['directory'])

                # Notify Trakt
                log.debug('Trakt')
                trakt = Trakt()
                trakt.notify(movie['movie'].name, movie['movie'].year, movie['movie'].imdb)

            else:
                path = movie['path'].split(os.sep)
                path.extend(['_UNKNOWN_' + path.pop()])
                target = os.sep.join(path)
                _move(movie['path'], target)

                log.info('No Match found for: %s' % str(movie['info']['name']))

            #Cleanup
            if self.conf('cleanup'):
                log.debug('cleanup')
                path = movie['path']

#                if self.conf('destination') == path:
#                    log.error('Download folder and movie destination shouldn\'t be the same. Change it in Settings >> Renaming.')
#                    return

                for root, subfiles, filenames in os.walk(path):
                    skip = False

                    # Stop if something is in ignored list
                    for ignore in self.ignoredInPath:
                        if ignore in root.lower():
                            skip = True

                    # Ignore full directory names
                    for dir in os.path.split(root):
                        if dir in self.ignoreNames:
                            skip = True

                    # ignore if the current dir is the blackhole
                    if root in self.conf('download'):
                        skip = True

                    if skip: continue

                    for filename in filenames:
                        fullFilePath = os.path.join(root, filename)
                        fileSize = os.path.getsize(fullFilePath)

                        if fileSize < 157286400:
                            try:
                                os.remove(fullFilePath)
                                log.info('Removing file %s.' % fullFilePath)
                            except OSError:
                                log.error('Couldn\'t remove file %s. Too large.' % fullFilePath)

                    try:
                        os.rmdir(root)
                        log.info('Removing dir: %s in download dir.' % root)
                    except OSError:
                        log.error("Tried to clean-up download folder, but '%s' isn't empty." % root)

    def genMetaFileName(self, movie, pattern, add_tags = None):
        moviename = movie['info'].get('name')

        # Put 'The' at the end
        namethe = moviename
        if moviename[:3].lower() == 'the':
            namethe = moviename[3:] + ', The'

        replacements = {
                        'namethe': namethe.strip(),
                        'thename': moviename.strip(),
                        'year': movie['info']['year'],
                        'first': namethe[0].upper(),
                        'quality': movie['info']['quality'],
                        'video': movie['info']['codec']['video'],
                        'audio': movie['info']['codec']['audio'],
                        'group': movie['info']['group'],
                        'resolution': movie['info']['resolution'],
                        'sourcemedia': movie['info']['sourcemedia']
                    }
        if add_tags:
            replacements.update(add_tags)

        return self.doReplace(pattern, replacements)


    def renameFiles(self, movie):
        '''
        rename files based on movie data & conf
        '''

        multiple = False
        if len(movie['files']) > 1:
            multiple = True

        destination = self.conf('destination')
        folderNaming = self.conf('foldernaming')
        fileNaming = self.conf('filenaming')

        # Remove weird chars from moviename
        moviename = re.sub(r"[\x00\/\\:\*\?\"<>\|]", '', movie['info'].get('name'))

        # Put 'The' at the end
        namethe = moviename
        if moviename[:4].lower() == 'the ':
            namethe = moviename[4:] + ', The'

        replacements = {
             'cd': '',
             'cdNr': '',
             'ext': 'mkv',
             'namethe': namethe.strip(),
             'thename': moviename.strip(),
             'year': movie['info']['year'],
             'first': namethe[0].upper(),
             'quality': movie['info']['quality'],
             'video': movie['info']['codec']['video'],
             'audio': movie['info']['codec']['audio'],
             'group': movie['info']['group'],
             'resolution': movie['info']['resolution'],
             'sourcemedia': movie['info']['sourcemedia']
        }

        if multiple:
            cd = 1

        justAdded = []
        finalDestination = None

        #clean up post-processing script
        ppScriptName = movie['info'].get('ppScriptName')
        ppDirName = self.config.get('Sabnzbd', 'ppDir')
        if ppScriptName:
            if ppDirName:
                ppPath = os.path.join(ppDirName, ppScriptName)
                try:
                    os.remove(ppPath)
                    log.info("Removed post-processing script: %s" % ppPath)
                except:
                    log.info("Couldn't remove post-processing script: %s" % ppPath)
            else:
                log.info("Don't know where the post processing script is located, not removing %s" % ppScriptName)

        filenames = []

        for file in movie['files']:
            log.info('Trying to find a home for: %s' % latinToAscii(file['filename']))

            replacements['ext'] = file['ext']

            if multiple:
                replacements['cd'] = ' cd' + str(cd)
                replacements['cdNr'] = ' ' + str(cd)

            replacements['original'] = file['filename']

            folder = self.doReplace(folderNaming, replacements)
            filename = self.doReplace(fileNaming, replacements)
            filenames.append(filename)

            old = os.path.join(movie['path'], file['filename'])
            dest = os.path.join(destination, folder, filename)

            finalDestination = os.path.dirname(dest)
            if not os.path.isdir(finalDestination):

                try:
                    log.info('Creating directory %s' % finalDestination)
                    os.makedirs(finalDestination)
                    shutil.copymode(destination, finalDestination)
                except OSError:
                    log.error('Failed changing permissions %s' % finalDestination)

            # Remove old if better quality
            removed = self.removeOld(os.path.join(destination, folder), justAdded, movie['info']['size'])

            if not os.path.isfile(dest) and removed:
                log.info('Moving file "%s" to %s.' % (latinToAscii(old), dest))

                if not _move(old, dest):
                    break
                justAdded.append(dest)
            else:
                try:
                    log.error('File %s already exists or not better.' % latinToAscii(filename))
                    path = movie['path'].split(os.sep)
                    path.extend(['_EXISTS_' + path.pop()])
                    old = movie['path']
                    dest = os.sep.join(path)
                    _move(old, dest)
                except:
                    log.error('Could not extend path name.')
                break

            #get subtitle if any & move
            for type in movie['subtitles']:
                if len(movie['subtitles'][type]) > 0:
                    log.info('Moving matching subtitle.')

                    subtitle = movie['subtitles'][type].pop(0)

                    replacements['original'] = subtitle['filename']
                    replacements['ext'] = subtitle['ext']

                    subDest = os.path.join(destination, folder, self.doReplace(fileNaming, replacements))
                    old = os.path.join(movie['path'], subtitle['filename'])
                    if not _move(old, subDest):
                        break
                    justAdded.append(subDest) # Add to ignore list when removing stuff.

            # Add to renaming history
            log.debug('renamehistory start')
            h = RenameHistory()
            Db.add(h)

            try:
                h.movieQueue = movie['queue'].id
            except:
                h.movieQueue = 0

            h.old = unicode(old.decode('utf-8'))
            h.new = unicode(dest.decode('utf-8'))
            Db.flush()
            log.debug('renamehistory end')

            if multiple:
                cd += 1

        # Mark movie downloaded
        log.debug('queue downloaded start')
        if movie['queue'] and movie['queue'].id > 0:
            if movie['queue'].markComplete:
                movie['movie'].status = u'downloaded'

            movie['queue'].completed = True
            Db.flush()
        log.debug('queue downloaded end')

        return {
            'directory': finalDestination,
            'filenames': filenames
        }

    def removeOld(self, path, dontDelete = [], newSize = 0):

        files = []
        oldSize = 0
        for root, subfiles, filenames in os.walk(path):
            log.debug(subfiles)

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()[1:]
                fullPath = os.path.join(root, filename)
                oldSize += os.path.getsize(fullPath)

                # iso's are huge, but the same size as 720p, so remove some filesize for better comparison
                if ext == 'iso':
                    oldSize -= (os.path.getsize(fullPath) / 1.6)

                if not fullPath in dontDelete:

                    # Only delete media files and subtitles
                    if ('*.' + ext in self.extensions['movie'] or '*.' + ext in self.extensions['subtitle']) and not '-trailer' in filename:
                        files.append(fullPath)

        log.info('Quality Old: %d, New %d.' % (long(oldSize) / 1024 / 1024, long(newSize) / 1024 / 1024))
        if long(oldSize) < long(newSize):
            for file in files:
                try:
                    os.remove(file)
                    log.info('Removed old file: %s' % file)
                except OSError:
                    log.info('Couldn\'t delete file: %s' % file)
            return True
        else:
            log.info('New file(s) are smaller then old ones, don\'t overwrite')
            return False


    def doReplace(self, string, replacements):
        '''
        replace confignames with the real thing
        '''

        replaced = string
        for x, r in replacements.iteritems():
            if r is not None:
                replaced = replaced.replace(u'<' + unicode(x) + u'>', unicode(r))
            else:
                #If information is not available, we don't want the tag in the filename
                replaced = replaced.replace('<' + x + '>', '')

        replaced = re.sub(r"[\x00:\*\?\"<>\|]", '', replaced)

        sep = self.conf('separator')
        return self.replaceDoubles(replaced).replace(' ', ' ' if not sep else sep)

    def replaceDoubles(self, string):
        return string.replace('  ', ' ').replace(' .', '.')
    
    def _run_extra_script(self, finalDestination):
        if (self.conf('script_enabled') and self.conf('file_path')):
            for file in finalDestination['filenames']:
                script_cmd = [os.path.abspath(self.conf('file_path'))] + [os.path.join(finalDestination['directory'], file)]
                log.info('Executing command: ' + str(script_cmd))
                try:
                    p = subprocess.Popen(script_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    out, err = p.communicate() #@UnusedVariable
                    log.info(u"Script result: "+str(out))
                except OSError, e:
                    log.info(u"Unable to run extra_script: " + str(e.args[1]))

def _move(old, dest, suppress = True):
    try:
        shutil.move(old, dest)
    except shutil.Error as exc:
        log.error("Couldn't move file '%s' to '%s'." % (old, dest))
        log.error(traceback.format_exc())
        if not suppress:
            raise exc
    else:
        return True

def startRenamerCron(config, searcher, debug):
    cron = RenamerCron()
    cron.config = config
    cron.debug = debug
    cron.searcher = searcher
    cron.trailerQueue = searcher.get('trailerQueue')
    cron.start()

    return cron
