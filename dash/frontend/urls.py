import api1
import json
from dash.frontend import app
from flask import request

@app.route('/')
def homepage():
    return app.send_static_file('index.html')

@app.route('/api/')
def api_no_version():
    data = { 
            'error': 'No API version supplied', 
            'v1': request.url_root+'api/1/',
            }
    return json.dumps(data)
