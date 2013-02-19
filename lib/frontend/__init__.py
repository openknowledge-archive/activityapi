from flask import Flask,request,make_response
import json

app = Flask('lib.frontend')
app.config.from_object('lib.frontend.settings')

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

# Patch the app with API v1 endpoints
import api1
