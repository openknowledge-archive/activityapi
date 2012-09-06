from dash.frontend import app
from dash.backend import Session
from dash.backend.model import *
from flask import request, make_response
from datetime import datetime,timedelta
import json
import functools
from sqlalchemy import func,select

##################################################
####           Utilities
##################################################

def endpoint(rule, **options):
    """Function decorator borrowed & modified from Flask core."""
    BASE='/api/1'
    def decorator(f):
        @functools.wraps(f)
        def wrapped_fn(*args, **kwargs):
            callback = request.args.get('callback')
            try:
                raw = f(*args, **kwargs)
            except (AssertionError, ValueError) as e:
                if request.args.get('_debug') is not None:
                    raise e
                raw = { 'ok': False, 'message' : e.message }
            response_text = json.dumps(raw)
            if callback:
                response_text = '%s(%s);' % (callback,response_text)
            response = make_response(response_text)
            response.headers['content-type'] = 'application/json'
            return response
        endpoint = options.pop('endpoint', None)
        app.add_url_rule(BASE+rule, endpoint, wrapped_fn, **options)
        return f
    return decorator

def _prepare(total=None, per_page=10):
    """Prepare a response object based off the incoming args (assume pagination)"""
    response = {}
    response['ok'] = True
    response['page'] = int(request.args.get('page',0))
    response['per_page'] = int(request.args.get('per_page',per_page))
    response['offset'] = response['per_page'] * response['page']
    assert response['page']>=0, 'Page number out of range.'
    assert response['per_page']>0, 'per_page out of range.'
    if total:
        response['total'] = total
        response['last_page'] = max(0,total-1) / response['per_page']
    return response

def _get_grain():
    grain = request.args.get('grain','day')
    valid = ['day', 'week', 'month', 'quarter', 'year']
    assert grain in valid, 'Grain must be one of: %s. (Got value: "%s")' % (json.dumps(valid), grain)
    return grain

def _count_group_by(group_by):
    """Count the number of rows a SELECT ... GROUP BY will return."""
    return engine.execute(\
                select([group_by])\
                    .group_by(group_by)\
                    .alias('tmp')\
                    .count()\
            )\
            .first()[0]

##################################################
####           URL: /
##################################################
@endpoint('/')
def index():
    rules = [x.rule for x in app.url_map.iter_rules()]
    endpoints = [request.url_root[:-1]+x for x in rules if x.startswith('/api/1')]
    return {'version':'1.0','ok':True,'endpoints':endpoints}


##################################################
####           URLS: /data/...
##################################################
@endpoint('/data/timestamp')
def data__timestamps():
    response = _prepare( Session.query(Timestamp).count() )
    q = Session.query(Timestamp)\
            .order_by(Timestamp.id.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ {'id':x.id,'now':x.now} for x in q ] 
    return response


##################################################
####           URLS: /activity/...
##################################################

##################################################
####           URLS: /history/...
##################################################
@endpoint('/history/twitter')
def history__twitter():
    response = _prepare( Session.query(SnapshotOfTwitter).count() )
    q = Session.query(SnapshotOfTwitter)\
            .order_by(SnapshotOfTwitter.timestamp.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ x.toJson() for x in q ] 
    return response

@endpoint('/history/github')
def history__github():
    response = _prepare( Session.query(SnapshotOfRepo).count() )
    q = Session.query(SnapshotOfRepo)\
            .order_by(SnapshotOfRepo.timestamp.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ x.toJson() for x in q ] 
    return response

@endpoint('/history/mailman')
def history__mailman_all(**args):
    assert False, 'Combined view-all-lists not yet implemented'

@endpoint('/history/mailman/<listname>')
def history__mailman(**args):
    mailman = Session.query(Mailman)\
            .filter(Mailman.name==args['listname'])\
            .first()
    assert mailman, 'list "%s" does not exist' % args['listname']
    grain = _get_grain()
    date_group = func.date_trunc(grain, SnapshotOfMailman.timestamp)
    # Count the results
    response = _prepare(_count_group_by(date_group))
    stmt = select([ date_group,\
                    func.sum(SnapshotOfMailman.posts_today),\
                    func.max(SnapshotOfMailman.subscribers)])\
            .group_by(date_group)\
            .where(SnapshotOfMailman.mailman_id==mailman.id)\
            .order_by(date_group.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    q = engine.execute(stmt)
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'timestamp':x[0].date().isoformat(),
        'posts':x[1],
        'subscribers':x[2]
    }
    response['data'] = [ _dictize(x) for x in q ] 
    response['grain'] = grain
    response['list_id'] = mailman.id
    response['list_name'] = mailman.name
    response['list_link'] = mailman.link
    response['list_description'] = mailman.description
    return response
    




##################################################
####           URLS: /debug/...
##################################################
@endpoint('/debug/twitter_ratelimit')
def debug__twitter_ratelimit():
    import dash.twitter
    api = dash.twitter._connect()
    return api.rate_limit_status()


@endpoint('/debug/request')
def debug__request():
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


def twitter_tweets():
    limit = 50
    count = Session.query(Tweet).count()
    q = Session.query(Tweet).order_by(Tweet.tweet_id.desc()).limit(limit)
    data = { 
        'total': count, 
        'limit': limit, 
        'data': [ tweet.toJson() for tweet in q ] 
    }
    return data


def trends_registered():
    since_days = 365
    now = datetime.now().date() 
    pointer = now - timedelta(days=since_days)
    # Rolling count of how many registered users there were
    num_people = Session.query(Person).filter(Person.registered<pointer).count()
    data = []
    q = Session.query(Person)\
            .filter(Person.registered>=pointer)\
            .order_by(Person.registered.desc()) 
    people = list(q)
    while pointer<now:
        names = []
        while people and people[-1].registered.date()<=pointer:
            names.append( people.pop().login )
        num_people += len(names)
        data.append({
            'date': pointer.isoformat(),
            'num_people':num_people,
            'new_users':names
        })
        pointer += timedelta(days=1)
    return {
        'total_users': num_people,
        'num_days': since_days,
        'history' : data
        }

def activity_user():
    username = request.args.get('username')
    assert username, 'Add ?username=... to your URL'
    user = Session.query(Person).filter(Person.login==username).first()
    assert user, 'Username not found'
    all_activity = bool( request.args.get('all') )
    grouped = not bool( request.args.get('seperate') )
    return _user_activity(user,grouped,all_activity)

def activity_staff():
    return _anyone_activity(True)

def activity_all():
    return _anyone_activity(False)

def _anyone_activity(staff_only=False):
    mails = Session.query(Person,ActivityInMailman)\
            .filter(Person.email==ActivityInMailman.email)
    if staff_only: mails = mails.filter(Person._opinion=='staff')
    mails = mails.order_by(ActivityInMailman.timestamp.desc())\
            .limit(10)
    tweets = Session.query(Person,Tweet)\
            .filter(Tweet.screen_name==Person.twitter)
    if staff_only: tweets = tweets.filter(Person._opinion=='staff')
    tweets = tweets.order_by(Tweet.timestamp.desc())\
            .limit(10)
    buddypress = Session.query(Person,ActivityInBuddypress)\
            .filter(ActivityInBuddypress.login==Person.login)
    if staff_only: buddypress = buddypress.filter(Person._opinion=='staff')
    buddypress = buddypress.order_by(ActivityInBuddypress.timestamp.desc())\
            .limit(10)
    github = Session.query(Person,ActivityInGithub)\
            .filter(ActivityInGithub.user_id==Person.id)
    if staff_only: github = github.filter(Person._opinion=='staff')
    github = github.order_by(ActivityInGithub.timestamp.desc())\
            .limit(10)
    def combine(user,obj):
        out = obj.toJson()
        out['login'] = user.login
        out['display_name'] = user.display_name
        return out
    return {
            'events_tweets':[ combine(u,x) for u,x in tweets ],
            'events_mails':[ combine(u,x) for u,x in mails ],
            'events_buddypress':[ combine(u,x) for u,x in buddypress ],
            'events_github':[ combine(u,x) for u,x in github ],
            }


def _user_activity(user,grouped,all_activity):
    _mails = Session.query(ActivityInMailman)\
            .filter(ActivityInMailman.email==user.email)
    mails = [ x.toJson() for x in _mails ]

    _tweets = Session.query(Tweet)\
            .filter(Tweet.screen_name==user.twitter)
    tweets = [ x.toJson() for x in _tweets ]

    _buddypress = Session.query(ActivityInBuddypress)\
            .filter(ActivityInBuddypress.login==user.login)
    buddypress = [ x.toJson() for x in _buddypress ]

    _github = Session.query(ActivityInGithub)\
            .filter(ActivityInGithub.user_id==user.id)
    github = [ x.toJson() for x in _github ]
    # Always sort lists by timestamp
    sortkey = lambda x : x['timestamp']
    # Grouped mode is the default behaviour...
    if grouped:
        grouped = []
        for x in mails:      x['_event_type']='mail';       grouped.append(x)
        for x in tweets:     x['_event_type']='tweet';      grouped.append(x)
        for x in buddypress: x['_event_type']='buddypress'; grouped.append(x)
        for x in github:     x['_event_type']='github';     grouped.append(x)
        grouped = sorted(grouped, key=sortkey,reverse=True)
        if not all_activity:
            grouped = grouped[:10]
        return {
            'username':user.login,
            'display_name':user.display_name,
            'events': grouped
        }

    mails = sorted(mails,key=sortkey,reverse=True)
    tweets = sorted(tweets,key=sortkey,reverse=True)
    buddypress = sorted(buddypress,key=sortkey,reverse=True)
    github = sorted(github,key=sortkey,reverse=True)
    # Trim output
    if not all_activity:
        mails = mails[:5]
        buddypress = buddypress[:5]
        tweets = tweets[:5]
        github = github[:5]
    return {
            'username':user.login,
            'display_name':user.display_name,
            'events_tweets':tweets,
            'events_mails':mails,
            'events_buddypress':buddypress,
            'events_github':github,
            }




def person_list():
    count = Session.query(Person).count()
    q = Session.query(Person).order_by(Person.user_id.desc())
    opinion = request.args.get('opinion',None)
    if opinion is not None:
        if opinion=='': opinion = None
        q = q.filter(Person._opinion==opinion)
    return { 
        'total': count, 
        'data': [ person.toJson() for person in q ] 
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
