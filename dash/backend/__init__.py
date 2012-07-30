import os
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    raise ValueError('No DATABASE_URL defined in the environment. Try running:\n          $ export DATABASE_URL=postgresql://user:pass@localhost/mydatabase')

engine = create_engine(database_url, echo=True)
Session = scoped_session(sessionmaker(engine))

import model

