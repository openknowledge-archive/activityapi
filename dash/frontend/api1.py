from dash.frontend import app
from dash.backend import Session
from dash.backend.model import *
import dash.util
from flask import request
from datetime import datetime,timedelta
import json

@app.route('/api/1/')
def index():
    rules = [x.rule for x in app.url_map.iter_rules()]
    endpoints = [request.url_root[:-1]+x for x in rules if x.startswith('/api/1')]
    return json.dumps({'version':'0.1','ok':True,'endpoints':endpoints})

@app.route('/api/1/debug/request')
def debug_request():
    """Dump the user's request back at them"""
    data = {
            'base_url' : request.base_url,
            'url_root' : request.url_root,
            'path' : request.path,
            'method' : request.method,
            'headers' : {k:v for k,v in request.headers.iteritems()},
            'args' : request.args,
            'view_args' : request.view_args,
    }
    return json.dumps(data)

@app.route('/api/1/twitter/tweets')
def twitter():
    limit = 50
    count = Session.query(Tweet).count()
    q = Session.query(Tweet).order_by(Tweet.tweet_id.desc()).limit(limit)
    data = { 
        'total': count, 
        'limit': limit, 
        'data': [ tweet.json() for tweet in q ] 
    }
    return json.dumps(data)

@app.route('/api/1/twitter/ratelimit')
def twitter_ratelimit():
    import dash.twitter
    api = dash.twitter.get_api()
    return json.dumps( api.rate_limit_status() )

@app.route('/api/1/twitter/trends')
def twitter_trends():
    hours = 12
    since = datetime.now() - timedelta(hours=hours)
    q = Session.query(Tweet).filter(Tweet.timestamp >= since)
    freq = dash.util.freq_table( q )
    data = {
        'since' : since.isoformat(),
        'since_hours' : hours,
        'count_tweets' : q.count(),
        'hashtags' : dash.util.analyse(freq,hashtags=True,results=5),
        'urls' : dash.util.analyse(freq,links=True,results=5),
        'words' : dash.util.analyse(freq)
    }
    return json.dumps( data )

@app.route('/api/1/timestamps')
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
