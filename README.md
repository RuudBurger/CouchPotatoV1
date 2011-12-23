CouchPotato
=====

CouchPotato (CP) is an automatic NZB and torrent downloader. You can keep a "movies I want"-list and it will search for NZBs/torrents of these movies every X hours.
Once a movie is found, it will send it to SABnzbd or download the torrent to a specified directory.

Features:

* Automatic downloading and sending of NZBs to SABnzbd
* Automatic downloading of torrents files to a specified directory
* Easily add movies via IMDB UserScript
* Movie sorting & renaming
* Trailer downloading
* Quality options to download best available. Overwrite if better is found.
* A "Coming Soon" page with soon to be released DVD and Theater info.
* Support for NZBs.org, NZBMatrix, Newznab.com and ThePirateBay.


![preview thumb](https://github.com/RuudBurger/CouchPotato/raw/master/media/images/screenshot.png)

UserScript:

![imdb](https://github.com/RuudBurger/CouchPotato/raw/master/media/images/userscriptPreview.png)

If you find a bug or need a feature that you think is awesome! Let me know!

## Donate

[![PayPal - Donate](https://www.paypal.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=GFWSRM6L43T2S&lc=US&item_name=A%20more%20awesome%20CouchPotato&currency_code=EUR&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted)

I'm building CouchPotato in my spare time, so if you want to buy me a coke while I'm coding, that would be awesome!


## Changelog

[Can be found here](https://github.com/RuudBurger/CouchPotato/blob/master/changelog.md)

## Todo

[Can be found here](https://github.com/RuudBurger/CouchPotato/blob/master/todo.md)

## Dependencies

To run CP you will need Python.

## CouchPotato is built using

[CherryPy](http://www.cherrypy.org/),
[SQLAlchemy](http://www.sqlalchemy.org/),
[Mako](http://www.makotemplates.org/),
[Routes](http://routes.groovie.org/),
[IMDbPy](http://imdbpy.sourceforge.net/),
[DateUtil](http://labix.org/python-dateutil),
[MarkupSafe](http://pypi.python.org/pypi/MarkupSafe),
[TheMovieDB](http://www.themoviedb.org/),
[NZBMatrix](http://nzbmatrix.com/),
[NZBs.org](http://www.nzbs.org/),
[Newznab.com](http://www.newznab.com/),
[HD-Trailers](http://www.hd-trailers.net/),
[The Pirate Bay](http://thepiratebay.org/),
[PyInstaller](http://www.pyinstaller.org/)




## Installation and Setup

Windows:

* Download the latest Windows build [Can be found here](https://github.com/RuudBurger/CouchPotato/downloads)
* Extract it wherever you like
* Start CouchPotato.exe
* Set your username & password in the settings if you want.
* Fill in all the config stuff

OSx:

* If you're on Leopard (10.5) install Python 2.6+: [Python 2.6.5](http://www.python.org/download/releases/2.6.5/)
* Git clone/extract CP wherever you like
* Run "CouchPotato.app"
* Set your username & password in the settings if you want.
* Fill in all the config stuff

Linux:

* Install Python 2.6 or higher
* Git clone/extract CP wherever you like
* Run "python CouchPotato.py -d" to start in deamon mode
* Set your username & password in the settings if you want.
* Fill in all the config stuff

Ubuntu (init.d script):

* Copy "initd.ubuntu" to /etc/init.d/couchpotato - > "sudo cp initd.ubuntu /etc/init.d/couchpotato"  
* Copy "default.ubuntu" to /etc/default/couchpotato - > "sudo cp default.ubuntu /etc/default/couchpotato"  
* Edit the required daemon settings in /etc/default/couchpotato - > editor /etc/default/couchpotato  
* If your CP installation isn't in "/opt/couchpotato/", make sure to change the path there also!  
* Make executable "sudo chmod a+x /etc/init.d/couchpotato"  
* Add it to the startup items: "sudo update-rc.d couchpotato defaults"  
* Start with "sudo service couchpotato start"  

Other

* [Synology Guide can be found here](http://synology.brickman.nl/syn_howto/HowTo%20-%20install%20CouchPotato.txt)  
* [Synology Package can be found here](http://synoblog.superzebulon.org/category/cp/)  
* [QNAP Guide can be found here](http://forums.sabnzbd.org/index.php?topic=4636.msg33541#msg33541)  
* [QNAP Package can be found here](http://forum.qnap.com/viewtopic.php?f=269&t=40596)  

## Update

Github users can use the built-in update feature (under Settings, or in the CP footer)

If you're running the Windows Binary Build, you have to shutdown CP and overwrite the .exe with the newer function.
Make sure your config.ini and data.db are untouched.
