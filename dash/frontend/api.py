from dash.backend import Session
from dash.backend.model import *
import json

def index():
    return json.dumps({'version':'0.1','ok':True})

def twitter():
    out = {'hello':'world'}
    return json.dumps(out)

def timestamps():
    limit = 10
    count = Session.query(Timestamp).count()
    q = Session.query(Timestamp).order_by(Timestamp.id.desc()).limit(limit)
    data = { 
        'total': count, 
        'limit': limit, 
        'data': [ [x.id,x.now] for x in q ] 
    }
    return json.dumps(data)
