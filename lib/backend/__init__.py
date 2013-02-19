import os
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session

database_url = os.environ.get('DATABASE_URL')
database_echo = os.environ.get('DATABASE_ECHO', '').lower()=='true'

if not database_url:
    raise ValueError('No DATABASE_URL defined in the environment. Try running:\n          $ export DATABASE_URL=postgresql://user:pass@localhost/mydatabase')

engine = create_engine(database_url,echo=database_echo)
Session = scoped_session(sessionmaker(engine))

import model

