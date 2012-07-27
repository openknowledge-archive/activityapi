from flask import Flask
try:
  from flaskext.sqlalchemy import SQLAlchemy
except ImportError:
  from flask.ext.sqlalchemy import SQLAlchemy

app = Flask('application')
app.config.from_object('application.settings')
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_CON
db = SQLAlchemy(app)

import urls
from models import *
