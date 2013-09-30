from app import version
from app.config.cplog import CPLog
from app.lib.provider.rss import rss
from cherrypy.process.plugins import SimplePlugin
from git.repository import LocalRepository
from imdb.parser.http.bsouplxml._bsoup import BeautifulSoup
from urllib2 import URLError
import cherrypy
import os
import re
import shutil
import tarfile
import time
import urllib2

log = CPLog(__name__)

class Updater(rss, SimplePlugin):

    git = 'git://github.com/RuudBurger/CouchPotato.git'
    url = 'https://github.com/RuudBurger/CouchPotato/tarball/master'
    downloads = 'https://github.com/RuudBurger/CouchPotato/downloads'
    timeout = 10
    running = False
    version = None
    updateAvailable = False
    updateVersion = None
    availableString = None
    lastCheck = 0

    def __init__(self, bus):
        SimplePlugin.__init__(self, bus)

    def start(self):
        self.basePath = cherrypy.config['basePath']
        self.runPath = cherrypy.config['runPath']
        self.cachePath = cherrypy.config['cachePath']
        self.isFrozen = cherrypy.config['frozen']
        self.debug = cherrypy.config['debug']
        self.updatePath = os.path.join(self.cachePath, 'updates')
        self.historyFile = os.path.join(self.updatePath, 'history.txt')

        self.repo = LocalRepository(self.basePath)

        # get back the .git dir
        if self.hasGit() and not self.isRepo():
            try:
                log.info('Updating CP to git version.')
                path = os.path.join(self.cachePath, 'temp_git')
                self.removeDir(path)
                repo = LocalRepository(path)
                repo.clone(self.git)
                self.replaceWith(path)
                self.removeDir(path)
            except Exception, e:
                log.error('Trying to rebuild the .git dir: %s' % e)

        if not os.path.isdir(self.updatePath):
            os.mkdir(self.updatePath)

        if not os.path.isfile(self.historyFile):
            self.history('UNKNOWN Build.')

    start.priority = 70

    def useUpdater(self):
        return cherrypy.config['config'].get('global', 'updater')

    def isRunning(self):
        return self.running

    def run(self):

        if self.isFrozen:
            return self.checkForUpdateWindows()
        else:
            log.info("Updating")
            self.running = True

            if self.hasGit() and self.isRepo():
                result = self.doGitUpdate()
            else:
                result = self.doUpdate()

            time.sleep(1)
            cherrypy.engine.restart()

            self.running = False
            return result

    def hasGit(self):
        try:
            version = self.repo.getGitVersion()
            return version[:2] == '1.'
        except:
            pass

        return False

    def isRepo(self):
        return os.path.isdir(os.path.join(self.runPath, '.git'))

    def getVersion(self, force = False, tryGit = True):

        if not self.version or force:
            if self.isFrozen:
                self.version = 'Windows build r%d' % version.windows
            else:
                if self.hasGit() and tryGit and self.isRepo():
                    try:
                        output = self.repo.getHead().hash
                        log.debug('Git version output: %s' % output.strip())
                        self.version = 'git-' + output[:7]
                    except Exception, e:
                        log.error('Failed using GIT, falling back on normal version check. %s' % e)
                        return self.getVersion(force, False)
                else:
                    handle = open(self.historyFile, "r")
                    lineList = handle.readlines()
                    handle.close()
                    self.version = lineList[-1].replace('RuudBurger-CouchPotato-', '').replace('.tar.gz', '')

        return self.version

    def checkForUpdate(self):

        if not self.useUpdater():
            return

        if not self.version:
            self.getVersion()

        if self.isFrozen:
            self.updateAvailable = self.checkForUpdateWindows()
        else:
            update = self.checkGitHubForUpdate()
            latest_commit = update.get('name').replace('RuudBurger-CouchPotato-', '').replace('.tar.gz', '')

            if self.hasGit() and self.isRepo():
                self.updateAvailable = latest_commit not in self.version
            elif update:
                history = open(self.historyFile, 'r').read()
                self.updateAvailable = update.get('name').replace('.tar.gz', '') not in history

            if self.updateAvailable:
                self.availableString = 'Update available'
                self.updateVersion = latest_commit
            else:
                self.availableString = 'No update available'

        self.lastCheck = time.time()
        log.info(self.availableString)

    def checkGitHubForUpdate(self):
        try:
            data = self.urlopen(self.url)
        except (IOError, URLError):
            log.error('Failed to open %s.' % self.url)
            return False

        try:
            try:
                name = data.info().get('Content-Disposition').split('filename=')[-1]
            except:
                name = data.geturl().split('/')[-1]
        except:
            name = 'UNKNOWN Build.'
            log.error('Something is wrong with the updater.')

        return {'name':name, 'data':data}


    def checkForUpdateWindows(self):
        try:
            data = urllib2.urlopen(self.downloads, timeout = self.timeout).read()
        except (IOError, URLError):
            log.error('Failed to open %s.' % self.downloads)
            return False

        try:
            html = BeautifulSoup(data)
            results = html.findAll('a', attrs = {'href':re.compile('/downloads/')})

            for link in results:
                if 'windows' in str(link.parent).lower():
                    downloadUrl = 'http://github.com' + link.get('href').replace(' ', '%20')
                    break

            if 'r' + str(version.windows) in downloadUrl:
                return False

            return downloadUrl

        except AttributeError:
            log.debug('Nothing found.')

        return False

    def doGitUpdate(self):
        try:
            self.repo.saveStash(time.time())
            self.repo.pull()
            return True
        except Exception, e:
            log.error('Failed updating via GIT: %s' % e)

        return False

    def doUpdate(self):
        update = self.checkGitHubForUpdate()
        if not update:
            return False

        name = update.get('name')
        data = update.get('data')

        destination = os.path.join(self.updatePath, update.get('name'))

        if not os.path.isfile(destination):
            # Remove older tarballs
            log.info('Removing old updates.')
            for file in os.listdir(self.updatePath):
                filename = os.path.join(self.updatePath, file)
                if os.path.isfile(filename) and not '.txt' in filename:
                    os.remove(filename);

            log.info('Downloading %s.' % name)
            with open(destination, 'wb') as f:
                f.write(data.read())

        log.info('Extracting.')
        tar = tarfile.open(destination)
        tar.extractall(path = self.updatePath)

        log.info('Moving updated files to CouchPotato root.')
        name = name.replace('.tar.gz', '')
        extractedPath = os.path.join(self.updatePath, name)
        self.replaceWith(extractedPath)

        self.history(name)
        log.info('Update to %s successful.' % name)
        return True

    def history(self, version):
        handle = open(self.historyFile, "a")
        handle.write(version + "\n")
        handle.close()

    def replaceWith(self, path):
        for root, subfiles, filenames in os.walk(path):
            #log.debug(subfiles)
            for filename in filenames:
                fromfile = os.path.join(root, filename)
                tofile = os.path.join(self.runPath, fromfile.replace(path + os.path.sep, ''))

                if not self.debug:
                    try:
                        os.remove(tofile)
                    except:
                        pass

                    try:
                        #os.renames(fromfile, tofile)
                        shutil.copy(fromfile, tofile)
                        os.remove(fromfile)
                    except Exception, e:
                        log.error('Failed overwriting file: %s' % e)

    def removeDir(self, dir):
        try:
            if os.path.isdir(dir):
                shutil.rmtree(dir)
        except OSError, inst:
            os.chmod(inst.filename, 0777)
            self.removeDir(dir)
