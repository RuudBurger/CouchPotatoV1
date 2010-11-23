CouchPotato
=====

Version 26 (not released):

* New: Preferred words for searching in "Settings >> General".
* New: Download meta-data. Poster, fanart, .nfo file.
* New: XBMC Notifications.
* Enhancement: Ability to disable the updater.
* Enhancement: Better movie detection when renaming.
* Enhancement: Settings page instead of popup.
* Enhancement: R5 DVD-R is allowed
* Enhancement: Added <resolution> and <sourcemedia> to renaming filenames.
* Fix: Updated updater for new GitHub download page layout.
* Fix: Images from TheMovieDB couldn't be downloaded.
* Fix: OpenSubtitle didn't always stay logged in.
* Fix: Move .idx files along with .sub files.
* ![And a lot more fixed here](https://github.com/RuudBurger/CouchPotato/compare/f60d448ad0...dfefbbc9c60aba77171c329406b6050313ce1823)

Version 25:

* New: Subtitles support using SubScene and OpenSubtitles
* Enhancement: Link to Changelog when new Windows Build is available.
* Enhancement: Better logging class.
* Enhancement: SQLAlchemy updated to 0.6.4, removed unused code.
* Enhancement: Optimized PNGs, Movie list and CSS.
* Enhancement: Movie manage page, beginning.
* Enhancement: Mootools 1.3
* Fix: NZBs.org needs API-key for RSS check.
* Fix: Don't bug out the search on invalid RSS feed.

Version 24:

* Enhancement: Use movie object to get extra movie information on startup.
* Fix: Would quit on startup, because of invalid tMDB xml.

Version 23:

* New: Newznab.com support
* Enhancement: "Scroll to top"-button
* Enhancement: Score points for AC3 and DTS
* Enhancement: Ability to re-add nzb/torrent and search for other version to download
* Enhancement: Rename trailer on overwrite with better quality
* Enhancement: Renamer, change word seperator to space, dash or dot
* Enhancement: Ability to disable providers
* Enhancement: Mark existing non-renameable downloads with _EXISTS_ 
* Fix: Better link to wanted, snatched downloaded
* Fix: Changed default BR-Rip maximum size
* Fix: Strip config string values
* Fix: Strip http:// off of host, if necessary
* Fix: Removed duplicate ETA search
* Fix: Ignore empty "ignore words"
* Fix: Use lowercase for better quality guessing
* Fix: Allow 720p in BR-Rip searches
