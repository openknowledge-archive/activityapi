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

def wrap(function):
    def out():
        callback = request.args.get('callback')
        out = json.dumps(function())
        if callback:
            return '%s(%s);' % (callback,out)
        return out
    return out

app.add_url_rule('/api/1/', 'api1.index', view_func=wrap(api1.index))
app.add_url_rule('/api/1/debug/request', 'api1.debug_request', view_func=wrap(api1.debug_request))
app.add_url_rule('/api/1/twitter/tweets', 'api1.twitter_tweets', view_func=wrap(api1.twitter_tweets))
app.add_url_rule('/api/1/twitter/ratelimit', 'api1.twitter_ratelimit', view_func=wrap(api1.twitter_ratelimit))
app.add_url_rule('/api/1/twitter/trends', 'api1.twitter_trends', view_func=wrap(api1.twitter_trends))
app.add_url_rule('/api/1/timestamps', 'api1.timestamps', view_func=wrap(api1.timestamps))
app.add_url_rule('/api/1/person/profile', 'api1.profile_list', view_func=wrap(api1.profile_list))
