from app import latinToAscii
from app.config.cplog import CPLog
from app.lib import hashFile
from app.lib.provider.subtitle.base import subtitleBase
from hashlib import md5
import base64
import cherrypy
import os
import time
import xmlrpclib
import zlib

log = CPLog(__name__)

class openSubtitles(subtitleBase):

    name = "OpenSubtitles"
    siteUrl = "http://www.opensubtitles.org/"
    searchUrl = "http://api.opensubtitles.org/xml-rpc"
    hashes = {}
    token = None

    def __init__(self, config, extensions):
        self.config = config
        self.extensions = extensions

    def conf(self, value):
        return self.config.get('Subtitles', value)

    def login(self):

        if not self.token:
            self.wait()
            self.server = xmlrpclib.Server(self.searchUrl)
            self.lastUse = time.time()

            try:
                log_result = self.server.LogIn("", "", "eng", "CouchPotato")
                self.token = log_result["token"]
                log.debug("Logged into OpenSubtitles %s." % self.token)
            except Exception:
                log.error("OpenSubtitles could not be contacted for login")
                self.token = None
                return False

        return True;

    def close(self):
        if self.token:
            self.server.close()
            self.token = None

    def find(self, movie):

        if not (self.isAvailable(self.siteUrl) and self.login()):
            return

        data = {
            'subtitles': [],
            'language': '',
            'download': self.download
        }

        self.wait()
        self.hashes = {}
        for lang in self.conf('languages').split(','):
            for file in movie['files']:
                filePath = os.path.join(movie['path'], file['filename'])
                info = self.getInfo(filePath)
                search = {
                    'moviehash': info.get('moviehash'),
                    'moviebytesize': info.get('moviebytesize'),
                    'sublanguageid': self.languages.get(lang.strip())
                }

                results = self.getItems(movie, file, search)
                sorted(results, self.sort)

                if len(results) > 0:
                    result = results.pop(0)
                    data['language'] = result['language']
                    data['subtitles'].append(result)

            if len(data['subtitles']) == len(movie['files']):
                return data

        self.lastUse = time.time()

        return data

    def getInfo(self, filePath):
        key = md5(latinToAscii(filePath)).digest()
        if not self.hashes.get(key):
            self.hashes[key] = {
                'moviehash': hashFile(filePath),
                'moviebytesize': str(os.path.getsize(filePath))
            }
        return self.hashes.get(key)

    def getItems(self, movie, file, params):

        subtitles = []
        results = []

        try:
            results = self.server.SearchSubtitles(self.token, [params])
        except Exception, e:
            log.error("Couldn\'t search OpenSubtitles: %s, token:%s, params:%s, result:%s" % (e, self.token, params, results))
            return subtitles

        if results.get('data'):
            for r in results['data']:
                if int(r['SubBad']) == 0:
                    item = {}
                    item['id'] = r['IDSubtitleFile']
                    item['name'] = r['SubFileName']
                    item['rating'] = r['SubDownloadsCnt']
                    item['link'] = r['SubDownloadLink']
                    item['hi'] = r['SubHearingImpaired']
                    item['language'] = r['ISO639']
                    item['forFile'] = file['filename']

                    if not self.alreadyDownloaded(movie['movie'], item['forFile'], item['id']):
                        subtitles.append(item)

        return subtitles

    def download(self, data):

        ids = []
        names = {}
        for subtitle in data['subtitles']:
            ids.append(subtitle['id'])
            names[subtitle['id']] = subtitle['name']

        try:
            self.wait()
            data = self.server.DownloadSubtitles(self.token, ids)
            self.lastUse = time.time()
            log.info('Subtitle download "%s" finished.' % subtitle['name'])
        except Exception, e:
            log.error('Failed to open %s.' % e)
            return None

        subtitlesFiles = []
        tempdir = cherrypy.config.get('cachePath')
        for base in data['data']:
            data = base['data']
            data = base64.b64decode(data)
            data = zlib.decompress(data, 15 + 32)

            tempSubtitleFile = os.path.join(tempdir, names[base['idsubtitlefile']])

            # Remove the old
            if os.path.isfile(tempSubtitleFile): os.remove(tempSubtitleFile)

            dump = open(tempSubtitleFile, "wb")
            dump.write(data)
            dump.close()

            subtitlesFiles.append(tempSubtitleFile)

        return subtitlesFiles

    def sort(self, a, b):
        if a.get('rating') > b.get('rating'):
            if a.get('hi') and not b.get('hi'):
                return 1
            if not a.get('hi') and b.get('hi'):
                return - 1

        if a.get('rating') < b.get('rating'):
            if b.get('hi') and not a.get('hi'):
                return 1
            if not b.get('hi') and a.get('hi'):
                return - 1

        return 0

    languages = {
        "en": "eng",
        "fr" : "fre",
        "hu": "hun",
        "cs": "cze",
        "pl" : "pol",
        "sk" : "slo",
        "pt" : "por",
        "pt-br" : "pob",
        "es" : "spa",
        "el" : "ell",
        "ar":"ara",
        'sq':'alb',
        "hy":"arm",
        "ay":"ass",
        "bs":"bos",
        "bg":"bul",
        "ca":"cat",
        "zh":"chi",
        "hr":"hrv",
        "da":"dan",
        "nl":"dut",
        "eo":"epo",
        "et":"est",
        "fi":"fin",
        "gl":"glg",
        "ka":"geo",
        "de":"ger",
        "he":"heb",
        "hi":"hin",
        "is":"ice",
        "id":"ind",
        "it":"ita",
        "ja":"jpn",
        "kk":"kaz",
        "ko":"kor",
        "lv":"lav",
        "lt":"lit",
        "lb":"ltz",
        "mk":"mac",
        "ms":"may",
        "no":"nor",
        "oc":"oci",
        "fa":"per",
        "ro":"rum",
        "ru":"rus",
        "sr":"scc",
        "sl":"slv",
        "sv":"swe",
        "th":"tha",
        "tr":"tur",
        "uk":"ukr",
        "vi":"vie"
    }
