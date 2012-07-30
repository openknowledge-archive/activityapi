from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, scoped_session
import settings

engine = create_engine(settings.DB_CON, echo=True)
Session = scoped_session(sessionmaker(engine))

import model

