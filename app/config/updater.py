from app import version
from app.config.cplog import CPLog
from cherrypy.process.plugins import SimplePlugin
from imdb.parser.http.bsouplxml._bsoup import BeautifulSoup
from urllib2 import URLError
import cherrypy
import os
import re
import subprocess
import tarfile
import time
import urllib2

log = CPLog(__name__)

class Updater(SimplePlugin):

    url = 'http://github.com/RuudBurger/CouchPotato/tarball/master'
    downloads = 'http://github.com/RuudBurger/CouchPotato/downloads'
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

        if not os.path.isdir(self.updatePath):
            os.mkdir(self.updatePath)

        if not os.path.isfile(self.historyFile):
            self.history('UNKNOWN Build.')

        self.checkForUpdateWindows()

    start.priority = 70

    def useUpdater(self):
        return cherrypy.config['config'].get('global', 'updater') and not self.hasGit()

    def isRunning(self):
        return self.running

    def run(self):

        if self.isFrozen:
            return self.checkForUpdateWindows()
        else:
            log.info("Updating")
            self.running = True

            result = self.doUpdate()

            time.sleep(1)
            cherrypy.engine.restart()

            self.running = False
            return result

    def hasGit(self):
        return os.path.isdir(os.path.join(self.runPath, '.git'))

    def getVersion(self, force = False, tryGit = True):

        if not self.version or force:
            if self.isFrozen:
                self.version = 'Windows build r%d' % version.windows
            else:
                if self.hasGit() and tryGit:
                    try:
                        gitPath = cherrypy.config['config'].get('global', 'git')
                        p = subprocess.Popen(gitPath + ' rev-parse HEAD', stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True, cwd = self.runPath)
                        output, err = p.communicate()
                        if err or 'fatal' in output.lower(): raise RuntimeError(err)
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
            if update:
                history = open(self.historyFile, 'r').read()
                self.updateAvailable = update.get('name').replace('.tar.gz', '') not in history

        if self.updateAvailable: 
          self.availableString = 'Update available'
          self.updateVersion = update.get('name').replace('RuudBurger-CouchPotato-', '').replace('.tar.gz', '')
        else:
          self.availableString = 'No update available'
 
        self.lastCheck = time.time()
        log.info(self.availableString)

    def checkGitHubForUpdate(self):
        try:
            data = urllib2.urlopen(self.url, timeout = self.timeout)
        except (IOError, URLError):
            log.error('Failed to open %s.' % self.url)
            return False

        name = data.geturl().split('/')[-1]
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
        for root, subfiles, filenames in os.walk(extractedPath):
            log.debug(subfiles)
            for filename in filenames:
                fromfile = os.path.join(root, filename)
                tofile = os.path.join(self.runPath, fromfile.replace(extractedPath + os.path.sep, ''))

                if not self.debug:
                    try:
                        os.remove(tofile)
                    except:
                        pass
                    os.renames(fromfile, tofile)

        self.history(name)
        log.info('Update to %s successful.' % name)
        return True

    def history(self, version):
        handle = open(self.historyFile, "a")
        handle.write(version + "\n")
        handle.close()
