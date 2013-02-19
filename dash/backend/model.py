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

class SnapshotOfFacebook(Base):
    __tablename__='snapshot_facebook'
    timestamp = Column(Date, primary_key=True) 
    likes = Column(Integer)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'likes': self.likes,
        }

class SnapshotOfMailchimp(Base):
    __tablename__='snapshot_mailchimp'
    timestamp = Column(Date, primary_key=True) 
    name = Column(String, primary_key=True)
    members = Column(Integer)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'name': self.name,
            'members': self.members,
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

class SnapshotOfTwitterAccount(Base):
    __tablename__='snapshot_twitteraccount'
    timestamp = Column(Date, primary_key=True) 
    screen_name = Column(String, primary_key=True)
    followers = Column(Integer)
    following = Column(Integer)
    tweets = Column(Integer)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'screen_name': self.screen_name,
            'followers': self.followers,
            'following': self.following,
            'tweets': self.tweets
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
        fields = [  'website', 'about', 'last_active',
                    'twitter', 'github', 'permalink', 'location',
                    'display_name', 'login', 'avatar', 
                    '_opinion' ]
        out = { x:self.__getattribute__(x) for x in fields }
        out['registered'] = self.registered.isoformat()
        return out

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
            'github_payload' : json.loads(self.payload),
        }

Base.metadata.create_all()
