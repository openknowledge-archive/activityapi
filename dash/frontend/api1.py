from dash.frontend import app,util
from dash.backend import Session
from dash.backend.model import *
from flask import request, make_response
from datetime import datetime,timedelta
import json

def index():
    rules = [x.rule for x in app.url_map.iter_rules()]
    endpoints = [request.url_root[:-1]+x for x in rules if x.startswith('/api/1')]
    return {'version':'0.1','ok':True,'endpoints':endpoints}

def debug_request():
    """Dump the user's request back at them"""
    return {
            'base_url' : request.base_url,
            'url_root' : request.url_root,
            'path' : request.path,
            'method' : request.method,
            'headers' : {k:v for k,v in request.headers.iteritems()},
            'args' : request.args,
            'form' : request.form,
            'view_args' : request.view_args,
    }

def debug_timestamps():
    limit = 10
    count = Session.query(Timestamp).count()
    q = Session.query(Timestamp).order_by(Timestamp.id.desc()).limit(limit)
    return { 
        'total': count, 
        'limit': limit, 
        'data': [ [x.id,x.now] for x in q ] 
    }

def twitter_tweets():
    limit = 50
    count = Session.query(Tweet).count()
    q = Session.query(Tweet).order_by(Tweet.tweet_id.desc()).limit(limit)
    data = { 
        'total': count, 
        'limit': limit, 
        'data': [ tweet.json() for tweet in q ] 
    }
    return data

def twitter_ratelimit():
    import dash.twitter
    api = dash.twitter._connect()
    return  api.rate_limit_status() 

def twitter_trends():
    hours = 12
    since = datetime.now() - timedelta(hours=hours)
    q = Session.query(Tweet).filter(Tweet.timestamp >= since)
    freq = util.freq_table( q )
    data = {
        'since' : since.isoformat(),
        'since_hours' : hours,
        'count_tweets' : q.count(),
        'hashtags' : util.analyse(freq,hashtags=True,results=5),
        'urls' : util.analyse(freq,links=True,results=5),
        'words' : util.analyse(freq)
    }
    return data 

def person_list():
    count = Session.query(Person).count()
    q = Session.query(Person).order_by(Person.user_id.desc())
    opinion = request.args.get('opinion',None)
    if opinion is not None:
        if opinion=='': opinion = None
        q = q.filter(Person._opinion==opinion)
    return { 
        'total': count, 
        'data': [ person.json() for person in q ] 
    }

def person_set_opinion():
    login = request.values.get('login')
    opinion = request.values.get('opinion')
    assert login 
    assert opinion
    q = Session.query(Person).filter(Person.login==login).update({Person._opinion:opinion})
    Session.commit()
    return {
        'ok': q>0,
        'login': login,
        'opinion': opinion,
        'updated':q
    }
