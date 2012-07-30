from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String
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

Base.metadata.create_all()
