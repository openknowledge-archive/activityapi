from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,DateTime,BigInteger,Float
from . import engine

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

Base.metadata.create_all()
