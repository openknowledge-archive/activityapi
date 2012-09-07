from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,DateTime,Date,BigInteger,Float,ForeignKey,Boolean
from . import engine
import json

Base = declarative_base(bind=engine)

class Timestamp(Base):
    __tablename__='timestamp'
    id = Column(Integer, primary_key=True)
    now = Column(String)
    def __init__(self, now):
        self.now = now
    def __repr__(self):
        return "<Ts('%s')>" % (self.now)

class Repo(Base):
    __tablename__='repo'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime) 
    description = Column(String) 
    fork = Column(Boolean) 
    full_name = Column(String) 
    homepage = Column(String) 
    html_url = Column(String)
    language = Column(String)
    def __init__(self, repo):
        self.update(repo)
    def update(self, repo):
        self.created_at = repo.created_at
        self.description = repo.description
        self.fork = repo.fork
        self.full_name = repo.full_name
        self.homepage = repo.homepage
        self.html_url = repo.html_url
        self.language = repo.language
    def toJson(self):
        return {
            'created_at' : self.created_at.isoformat() ,
            'description' : self.description ,
            'fork' : self.fork ,
            'full_name' : self.full_name ,
            'homepage' : self.homepage ,
            'html_url' : self.html_url ,
            'language' : self.language ,
        }

class SnapshotOfTwitter(Base):
    __tablename__='snapshot_twitter'
    timestamp = Column(Date, primary_key=True) 
    tweets_today = Column(Integer)
    hashtags = Column(String)
    links = Column(String)
    words = Column(String)
    authors = Column(String)
    def __init__(self, timestamp, tweets_today, hashtags, links, words, authors):
        self.timestamp = timestamp
        self.tweets_today = tweets_today 
        self.hashtags = json.dumps(hashtags)
        self.links = json.dumps(links)
        self.words = json.dumps(words)
        self.authors = json.dumps(authors)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'tweets_today': self.tweets_today,
            'hashtags': json.loads(self.hashtags),
            'links': json.loads(self.links),
            'words': json.loads(self.words),
            'authors': json.loads(self.authors),
        }


class SnapshotOfRepo(Base):
    __tablename__='snapshot_repo'
    repo_id = Column(Integer, ForeignKey('repo.id'), primary_key=True)
    timestamp = Column(Date, primary_key=True) 
    open_issues = Column(Integer)
    size = Column(Integer)
    watchers = Column(Integer)
    forks = Column(Integer)
    def __init__(self, timestamp, repo_id, open_issues, size, watchers, forks):
        self.repo_id = repo_id
        self.timestamp = timestamp
        self.open_issues = open_issues
        self.size = size
        self.watchers = watchers
        self.forks = forks
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'open_issues': self.open_issues,
            'size': self.size,
            'watchers': self.watchers,
            'forks': self.forks ,
        }


class Mailman(Base):
    __tablename__='mailman'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    link = Column(String)
    description = Column(String)
    def __init__(self, name, link, description):
        self.update(name,link,description)
    def update(self, name, link, description):
        self.name = name
        self.link = link
        self.description = description
    def toJson(self):
        return {
                'name': self.name,
                'link': self.link,
                'description': self.description,
                }

class SnapshotOfMailman(Base):
    __tablename__='snapshot_mailman'
    mailman_id = Column(Integer, ForeignKey('mailman.id'), primary_key=True)
    timestamp = Column(Date, primary_key=True) 
    subscribers = Column(Integer)
    posts_today = Column(Integer)
    def __init__(self, timestamp, mailman_id, subscribers, posts_today):
        self.mailman_id = mailman_id
        self.timestamp = timestamp
        self.subscribers = subscribers
        self.posts_today = posts_today
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'subscribers': self.subscribers,
            'posts_today': self.posts_today,
        }


class SnapshotOfBuddypress(Base):
    __tablename__='snapshot_buddypress'
    timestamp = Column(Date, primary_key=True) 
    num_users = Column(Integer)
    def __init__(self, timestamp, num_users):
        self.timestamp = timestamp
        self.num_users = num_users
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'num_users': self.num_users
        }


class Tweet(Base):
    __tablename__='activity_twitter'
    id = Column(Integer, primary_key=True)
    tweet_id = Column(BigInteger)
    timestamp = Column(DateTime)
    geo_x = Column(Float)
    geo_y = Column(Float)
    screen_name = Column(String)
    text = Column(String)
    @classmethod
    def parse(cls, raw_tweet):
        out = cls()
        out.screen_name = unicode(raw_tweet.user.screen_name),
        out.text = unicode(raw_tweet.text),
        out.tweet_id = raw_tweet.id
        out.timestamp = raw_tweet.created_at,
        if raw_tweet.geo:
            try:
                out.geo_x = float(raw_tweet.geo['coordinates'][0])
                out.geo_y = float(raw_tweet.geo['coordinates'][1])
            except IndexError:
                print 'ERROR handling geo: %s' % raw_tweet.geo
        return out
    def get_geo(self):
        if self.geo_x and self.geo_y:
            return [self.geo_x, self.geo_y]

    def toJson(self):
        out = self.__dict__
        return {
            'id': self.id,
            'tweet_id': self.tweet_id,
            'timestamp': self.timestamp.isoformat(),
            'screen_name': self.screen_name,
            'geo': self.get_geo(),
            'text':self.text
        }

class Person(Base):
    __tablename__='person'
    id = Column(Integer, primary_key=True)
    website = Column(String)
    about = Column(String)
    user_id = Column(Integer)
    last_active = Column(String)
    twitter = Column(String)
    registered_string = Column(String)
    registered = Column(DateTime)
    permalink = Column(String)
    location = Column(String)
    display_name = Column(String)
    login = Column(String)
    email = Column(String)
    github = Column(String)
    avatar = Column(String)
    _opinion = Column(String)
    _projects = Column(String)
    _twitter = Column(String)
    @classmethod
    def parse(cls, source_dict):
        out = cls()
        for (k,v) in source_dict.items():
            out.__setattr__(k, v)
        return out
    def toJson(self):
        fields = [  'website', 'about', 'user_id', 'last_active',
                    'twitter', 'permalink', 'location',
                    'display_name', 'login', 'email', 'avatar', 
                    '_opinion', '_projects']
        out = { x:self.__getattribute__(x) for x in fields }
        out['registered'] = self.registered.isoformat()
        return out

class ActivityInBuddypress(Base):
    __tablename__='activity_buddypress'
    id = Column(Integer, primary_key=True)
    login = Column(String)
    type = Column(String)
    timestamp = Column(DateTime)
    timestamp_string = Column(String)
    json = Column(String)
    def __init__(self, type, person, metadata={}, timestamp=None):
        if not timestamp:
            import datetime
            timestamp = datetime.datetime.now()
        self.login = person.login
        self.timestamp = timestamp
        self.type = type
        metadata['display_name'] = person.display_name
        self.json = json.dumps(metadata)
    def __repr__(self):
        if self.type=='add':
            return 'Added new user %s' % self.login
        if self.type=='delete':
            return 'Deleted user %s' % self.login
        if self.type=='update':
            return 'User %s updated profile (json=%s)' % (self.login, self.json[:50])
        return 'ActivityInBuddypress (type=%s login=%s)' % (self.type,self.login)
    def toJson(self):
        return {
            'login':self.login,
            'type':self.type,
            'timestamp':self.timestamp.isoformat(),
            'json':self.json,
        }

class ActivityInMailman(Base):
    __tablename__='activity_mailman'
    mailman_id  = Column(Integer, primary_key=True)
    message_id = Column(Integer, primary_key=True)
    subject = Column(String)
    author = Column(String)
    email = Column(String)
    link = Column(String)
    timestamp = Column(DateTime)
    def __init__(self, mailman_id, message_id, subject, author, email, link, timestamp):
        self.mailman_id = mailman_id
        self.message_id = message_id
        self.subject = subject
        self.author = author
        self.email = email
        self.link = link
        self.timestamp = timestamp
    def toJson(self):
        return {
            'message_id' : self.message_id,
            'subject' : self.subject,
            'author' : self.author,
            'email' : self.email,
            'link' : self.link,
            'timestamp' : self.timestamp.isoformat(),
        }

class ActivityInGithub(Base):
    __tablename__='activity_github'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    timestamp = Column(DateTime)
    timestamp_string = Column(String)
    type = Column(String)
    repo = Column(String)
    payload = Column(String)
    def __init__(self, user_id, event):
        self.id = int(event.id)
        self.user_id = user_id
        self.timestamp = event.created_at
        self.type = event.type
        self.repo = event.repo.name
        self.payload = json.dumps(event.payload)
    def toJson(self):
        return {
            'id' : self.id,
            'timestamp' : self.timestamp.isoformat(),
            'type' : self.type,
            'repo' : self.repo,
            'payload' : self.payload,
        }

Base.metadata.create_all()
