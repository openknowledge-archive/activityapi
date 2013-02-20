from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,DateTime,Date,BigInteger,Float,ForeignKey,Boolean
from . import engine
import json

Base = declarative_base(bind=engine)

class SnapshotOfGithub(Base):
    __tablename__='snapshot_github2'
    repo_name = Column(String,primary_key=True)
    timestamp = Column(Date, primary_key=True) 
    open_issues = Column(Integer)
    size = Column(Integer)
    watchers = Column(Integer)
    forks = Column(Integer)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'open_issues': self.open_issues,
            'size': self.size,
            'watchers': self.watchers,
            'forks': self.forks ,
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
    list_name = Column(String, primary_key=True)
    timestamp = Column(Date, primary_key=True) 
    subscribers = Column(Integer)
    posts_today = Column(Integer)
    def toJson(self):
        return {
            'list_name': self.list_name,
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

class SnapshotOfAnalytics(Base):
    __tablename__='snapshot_analytics'
    timestamp = Column(Date, primary_key=True) 
    website = Column(String, primary_key=True)
    hits = Column(Integer)
    def toJson(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'hits': self.hits,
        }

class ActivityInMailman(Base):
    __tablename__='activity_mailman'
    list_name  = Column(String, primary_key=True)
    message_id = Column(Integer, primary_key=True)
    subject = Column(String)
    author = Column(String)
    email = Column(String)
    link = Column(String)
    timestamp = Column(DateTime)
    def toJson(self):
        return {
            'message_id' : self.message_id,
            'subject' : self.subject,
            'author' : self.author,
            'email' : self.email,
            'link' : self.link,
            'timestamp' : self.timestamp.isoformat(),
        }
Base.metadata.create_all()
