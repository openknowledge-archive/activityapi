from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String

Base = declarative_base()

class Ts(Base):
  __tablename__='timestamps'
  id = Column(Integer, primary_key=True)
  now = Column(String)
  def __init__(self, now):
      self.now = now
  def __repr__(self):
     return "<Ts('%s')>" % (self.now)
