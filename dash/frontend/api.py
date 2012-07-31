from dash.backend import Session
import json

def index():
    return json.dumps({'version':'0.1','ok':True})

def twitter():
    out = {'hello':'world'}
    return json.dumps(out)
