from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask('application')
app.config.from_object('application.settings')
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_CON
db = SQLAlchemy(app)

class User(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   email = db.Column(db.String(128), unique=True)

   def __init__(self, id, email):
      self.id = id
      self.email = email

   def __repr__(self):
      return '<User %r>' % self.email

import urls
from models import *
