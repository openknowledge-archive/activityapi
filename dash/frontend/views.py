import os
from dash.backend import Session
from flask import render_template
from flask import request
from models import Ts

def index():
   return render_template('index.html', data='index page')

def timestamps():
   result = [ str(i) for i in Session.query(Ts).order_by(Ts.id) ]
   text = '\n'.join(result)
   return render_template('index.html', data=text)
