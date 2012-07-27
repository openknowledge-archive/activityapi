import os
from application import User
from application import db
from flask import render_template
from flask import request
from flask.ext.wtf import Form
from flask.ext.wtf import TextField
from models import Ts

class Invite(Form):
   email = TextField("Email")

def index():
   form = Invite(csrf_enabled=False)
   print db
   print os.environ.get('DATABASE_URL')
   return render_template('index.html', form=form)

def getinvite():
   print 'Requesting invitation'
   print db
   print os.environ.get('DATABASE_URL')
   form = Invite(request.form)
   print form.email.data
   user = User(None, form.email.data)
   db.session.add(user)
   db.session.commit()
   return render_template('index.html', form=form)

def timestamps():
   result = [ str(i) for i in db.session.query(Ts).order_by(Ts.id) ]
   text = '\n'.join(result)
   return render_template('index.html', data=text)
