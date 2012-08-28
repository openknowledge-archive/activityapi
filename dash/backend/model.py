from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,DateTime,BigInteger,Float,ForeignKey
from . import engine
import json

Base = declarative_base(bind=engine)

class Timestamp(Base):
    __tablename__='timestamps'
    id = Column(Integer, primary_key=True)
    now = Column(String)
    def __init__(self, now):
        self.now = now
    def __repr__(self):
        return "<Ts('%s')>" % (self.now)

class Tweet(Base):
    __tablename__='tweets'
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

    def json(self):
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
    __tablename__='people'
    id = Column(Integer, primary_key=True)
    website = Column(String)
    about = Column(String)
    user_id = Column(Integer)
    last_active = Column(String)
    twitter = Column(String)
    registered = Column(String)
    permalink = Column(String)
    location = Column(String)
    display_name = Column(String)
    login = Column(String)
    email = Column(String)
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
    def json(self):
        fields = [  'website', 'about', 'user_id', 'last_active',
                    'twitter', 'registered', 'permalink', 'location',
                    'display_name', 'login', 'email', 'avatar', 
                    '_opinion', '_projects']
        out = { x:self.__getattribute__(x) for x in fields }
        return out

class PersonDiff(Base):
    __tablename__='person_diff'
    id = Column(Integer, primary_key=True)
    login = Column(String)
    type = Column(String)
    timestamp = Column(String)
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
        return 'Persondiff [type=%s timestamp=%s login=%s json=%s]' % (self.type,self.timestamp,self.login,self.json)


Base.metadata.create_all()
