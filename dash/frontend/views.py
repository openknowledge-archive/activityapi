from dash.backend import Session
from dash.backend.model import Timestamp
from flask import render_template
from flask import request

def index():
   return render_template('index.html', data='index page')

def timestamps():
   result = [ str(i) for i in Session.query(Timestamp).order_by(Timestamp.id) ]
   text = '\n'.join(result)
   return render_template('index.html', data=text)
