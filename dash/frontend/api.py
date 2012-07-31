from dash.backend import Session
from dash.backend.model import *
import json

def index():
    return json.dumps({'version':'0.1','ok':True})

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

def twitter_ratelimit():
    import dash.twitter
    api = dash.twitter.get_api()
    return json.dumps( api.rate_limit_status() )

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
