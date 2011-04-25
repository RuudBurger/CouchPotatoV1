from app.config.cplog import CPLog
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, NoSuchTableError
from sqlalchemy.ext.sqlsoup import SqlSoup
from sqlalchemy.orm import mapper, relation, scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
from sqlalchemy.sql.expression import and_, desc
from sqlalchemy.types import Integer, DateTime, String, Boolean, Text
import datetime
import os
import sys
import app.config

log = CPLog(__name__)

try:
    frozen = sys.frozen
except AttributeError:
    frozen = False

if os.name == 'nt':
    if frozen:
        path = os.path.join(os.path.dirname(sys.executable), 'data.db')
    else:
        path = os.path.join(os.path.abspath(os.path.curdir), 'data.db')
else:
    path = os.path.join(app.config.DATADIR, 'data.db')

engine = create_engine('sqlite:///%s' % path)
metadata = MetaData(engine)
Session = scoped_session(sessionmaker(bind = engine, autocommit = True))

# DB VERSION
latestDatabaseVersion = 4

dbVersionTable = Table('DbVersion', metadata,
                     Column('version', Integer, primary_key = True)
            )

movieTable = Table('Movie', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('dateAdded', DateTime(), default = datetime.datetime.utcnow),
                     Column('dateChanged', DateTime(), default = datetime.datetime.utcnow),
                     Column('name', String()),
                     Column('year', Integer),
                     Column('imdb', String()),
                     Column('status', String()),
                     Column('quality', String(), ForeignKey('QualityTemplate.id')),
                     Column('movieDb', String())
            )

movieQueueTable = Table('MovieQueue', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movieId', Integer, ForeignKey('Movie.id')),
                     Column('qualityType', String()),
                     Column('date', DateTime(), default = datetime.datetime.utcnow),
                     Column('order', Integer),
                     Column('active', Boolean),
                     Column('completed', Boolean),
                     Column('waitFor', Integer, default = 0),
                     Column('markComplete', Boolean),
                     Column('name', String()),
                     Column('link', String()),
                     Column('lastCheck', Integer)
            )

movieEtaTable = Table('MovieETA', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movieId', Integer, ForeignKey('Movie.id')),
                     Column('videoEtaId', Integer),
                     Column('theater', Integer),
                     Column('dvd', Integer),
                     Column('bluray', Boolean),
                     Column('lastCheck', Integer)
            )

movieExtraTable = Table('MovieExtra', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movieId', Integer, ForeignKey('Movie.id')),
                     Column('name', String()),
                     Column('value', Text())
            )

renameHistoryTable = Table('RenameHistory', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movieQueue', Integer, ForeignKey('MovieQueue.id')),
                     Column('old', String()),
                     Column('new', String())
            )

historyTable = Table('History', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movie', Integer, ForeignKey('Movie.id')),
                     Column('value', String()),
                     Column('status', String())
            )

subtitleHistoryTable = Table('SubtitleHistory', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('movie', Integer, ForeignKey('Movie.id')),
                     Column('file', String()),
                     Column('subtitle', String()),
                     Column('status', String()),
                     Column('data', Text())
            )

qualityTemplateTable = Table('QualityTemplate', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('name', Integer, unique = True),
                     Column('label', String()),
                     Column('order', Integer),
                     Column('waitFor', Integer, default = 0),
                     Column('custom', Boolean),
                     Column('default', Boolean)
            )

qualityTemplateTypeTable = Table('QualityTemplateType', metadata,
                     Column('id', Integer, primary_key = True),
                     Column('quality', Integer, ForeignKey('QualityTemplate.id')),
                     Column('order', Integer),
                     Column('type', String()),
                     Column('markComplete', Boolean)
            )

class DbVersion(object):
    def __init__(self, version):
        self.version = version

    def __repr__(self):
        return "<dbversion: %s" % self.version

class Movie(object):
    name = None
    status = None
    dateChanged = None

    def __repr__(self):
        return "<movie: %s" % self.name

class MovieQueue(object):
    active = None
    complete = None
    order = None

    def __repr__(self):
        return "<moviequeue: %s active=%s complete=%s quality=%s" % (self.Movie.name, self.active, self.complete, self.qualityType)

class MovieETA(object):
    dvd = 0
    theater = 0
    bluray = 0
    lastCheck = 0

    def __repr__(self):
        return "<movieeta: %s" % self.videoEtaId

class MovieExtra(object):
    movieId = None
    name = None
    def __repr__(self):
        return "<movieextra: %s, %s" % (self.name, self.value)

class RenameHistory(object):
    def __repr__(self):
        return "<renamehistory: %s" % self.movieQueue

class History(object):
    movie = None
    status = None
    value = None

    def __repr__(self):
        return "<history: value=%s status=%s" % (self.value, self.status)

class SubtitleHistory(object):
    movie = None
    status = None
    file = None
    subtitle = None
    data = None

    def __repr__(self):
        return "<history: file=%s data=%s" % (self.file, self.data)

class QualityTemplate(object):
    id = None
    name = None
    order = None
    custom = None

    def __repr__(self):
        return self.name

class QualityTemplateType(object):
    order = None

    def __repr__(self):
        return "<qualitytempatetypes: %s" % self.type

# Mappers
versionMapper = mapper(DbVersion, dbVersionTable)
movieMapper = mapper(Movie, movieTable, properties = {
   'queue': relation(MovieQueue, backref = 'Movie', primaryjoin =
                and_(movieQueueTable.c.movieId == movieTable.c.id,
                movieQueueTable.c.active == True), order_by = movieQueueTable.c.order),
   'template': relation(QualityTemplate, backref = 'Movie'),
   'eta': relation(MovieETA, backref = 'Movie', uselist = False, viewonly = True),
   'extra': relation(MovieExtra, backref = 'Movie', viewonly = True),
   'history': relation(History, backref = 'Movie')
})
movieQueueMapper = mapper(MovieQueue, movieQueueTable, properties = {
    'renamehistory': relation(RenameHistory, backref = 'MovieQueue')
})
movieEtaMapper = mapper(MovieETA, movieEtaTable)
movieExtraMapper = mapper(MovieExtra, movieExtraTable)
renameHistoryMapper = mapper(RenameHistory, renameHistoryTable)
HistoryMapper = mapper(History, historyTable)
SubtitleHistoryMapper = mapper(SubtitleHistory, subtitleHistoryTable)
qualityMapper = mapper(QualityTemplate, qualityTemplateTable, properties = {
   'types': relation(QualityTemplateType, backref = 'QualityTemplate', order_by = qualityTemplateTypeTable.c.order)
})
qualityCustomMapper = mapper(QualityTemplateType, qualityTemplateTypeTable)

def initDb():
    log.info('Initializing Database.')

    # DB exists, do upgrade
    if os.path.isfile(path):
        doUpgrade = True;
    else:
        doUpgrade = False

    metadata.create_all()

    # set default qualities
    from app.lib.qualities import Qualities
    qu = Qualities()
    qu.initDefaults()

    if doUpgrade:
        upgradeDb()
    else:
        for nr in range(1, latestDatabaseVersion + 1):
            Session.add(DbVersion(nr))
            Session.flush()

def upgradeDb():

    currentVersion = Session.query(DbVersion).order_by(desc(DbVersion.version)).first()
    if currentVersion:
        if currentVersion.version == latestDatabaseVersion:
            log.debug('Database is up to date.')
            return

        if currentVersion.version < 2: migrateVersion2()
        if currentVersion.version < 3: migrateVersion3()
        if currentVersion.version < 4: migrateVersion4()
    else: # assume version 2
        migrateVersion3()

def migrateVersion4():
    log.info('Upgrading DB to version 4.')

    # for some normal executions
    db = SqlSoup(engine)

    try:
        db.execute('ALTER TABLE MovieETA ADD lastCheck INTEGER')
        log.info('Added lastCheck to MovieETA table')
    except OperationalError:
        log.debug('Column lastCheck already added.')

    try:
        db.execute('ALTER TABLE MovieQueue ADD lastCheck INTEGER')
        log.info('Added lastCheck to MovieQueue table')
    except OperationalError:
        log.debug('Column lastCheck already added.')

    Session.add(DbVersion(4))
    Session.flush()

def migrateVersion3():
    log.info('Upgrading DB to version 3.')

    # for some normal executions
    db = SqlSoup(engine)

    try:
        db.execute('ALTER TABLE Movie ADD dateChanged TIMESTAMP')
        log.info('Added dateChanged to Movie table')
    except OperationalError:
        log.debug('Column dateChanged already added')

    Session.add(DbVersion(3))
    Session.flush()

def migrateVersion2():
    log.info('Upgrading DB to version 2.')

    # for some normal executions
    db = SqlSoup(engine)

    # Remove not used table
    try:
        db.execute('DROP TABLE Feed')
        log.info('Removed old Feed table.')
    except (OperationalError, NoSuchTableError):
        log.debug('No Feed table found.')

    # History add column
    try:
        db.execute('DROP TABLE History')
        log.info('Removed History table.')
    except (OperationalError, NoSuchTableError):
        log.debug('No History table found.')

    # RenameHistory add column
    try:
        Session.query(RenameHistory).filter_by(movieQueue = '').all()
        log.debug('Column "RenameHistory:movieQueue" exists, not necessary.')
    except (OperationalError, NoSuchTableError):
        db.execute("CREATE TABLE RenameHistoryBackup(id, movieId, old, new);")
        db.execute("INSERT INTO RenameHistoryBackup SELECT id, movieId, old, new FROM RenameHistory;")
        db.execute("DROP TABLE RenameHistory;")
        db.execute("CREATE TABLE RenameHistory (id, movieQueue, old VARCHAR, new VARCHAR);")
        db.execute("INSERT INTO RenameHistory SELECT id, movieId, old, new FROM RenameHistoryBackup;")
        db.execute("DROP TABLE RenameHistoryBackup;")
        log.info('Added "movieQueue" column to existing RenameHistory Table.')

    # Mark all history

    # Quality from string to int
    movies = Session.query(Movie).all()
    for movie in movies:

        # Add moviequeues
        log.info('Making Queue item for %s' % movie.name)
        queue = MovieQueue()
        queue.movieId = movie.id
        queue.qualityType = movie.quality if movie.quality else 'dvdrip' #just for backup
        queue.order = 1
        queue.active = (movie.status != u'deleted')
        queue.completed = (movie.status != u'want')
        queue.markComplete = True
        Session.add(queue)
        Session.flush()

        log.info('Doing some stuff to RenameHistory')
        history = Session.query(RenameHistory).filter_by(movieQueue = movie.id).first()
        if history:
            history.movieQueue = queue.id
            queue.name = os.path.basename(os.path.dirname(history.old))
            Session.flush()

    Session.add(DbVersion(1)) # Add version 1 for teh nice
    Session.add(DbVersion(2))
    Session.flush()

