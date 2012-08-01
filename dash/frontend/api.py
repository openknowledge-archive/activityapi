from dash.backend import Session
from dash.backend.model import *
from datetime import datetime,timedelta
import json
import dash.util

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
