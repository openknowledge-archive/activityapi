from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine('postgresql://localhost/zephod', echo=True)
Session = scoped_session(sessionmaker(engine))

import model

