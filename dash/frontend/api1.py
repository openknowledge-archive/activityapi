from dash.frontend import app
from dash.backend import Session
from dash.backend.model import *
from flask import request, make_response
from datetime import datetime,timedelta
import json
import functools
from sqlalchemy import func,select
from urllib import urlencode

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

def _count_group_by(grouping):
    """Count the number of rows a SELECT ... GROUP BY will return."""
    return engine.execute(\
                select([grouping])\
                    .group_by(grouping)\
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
def data__timestamp():
    response = _prepare( Session.query(Timestamp).count() )
    q = Session.query(Timestamp)\
            .order_by(Timestamp.id.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ {'id':x.id,'now':x.now} for x in q ] 
    return response

@endpoint('/data/github')
def data__github():
    """Unpaginated -- there are less than 200 entries in the database"""
    response = {'ok' : True}
    q = Session.query(Repo).order_by(Repo.full_name)
    response['data'] = [ x.toJson() for x in q ]
    response['total'] = q.count()
    return response

@endpoint('/data/mailman')
def data__mailman():
    """Unpaginated -- there are less than 200 entries in the database"""
    response = {'ok' : True}
    q = Session.query(Mailman).order_by(Mailman.name)
    response['data'] = [ x.toJson() for x in q ]
    response['total'] = q.count()
    return response

@endpoint('/data/person')
def data__person():
    opinion = request.args.get('opinion',None)
    login = request.args.get('login',None)
    q = Session.query(Person).order_by(Person.user_id.desc())
    if opinion is not None:
        if opinion=='': opinion = None
        q = q.filter(Person._opinion==opinion)
    if login is not None:
        login = login.split(',')
        q = q.filter(Person.login.in_(login))
    response = _prepare(q.count())
    q = q.offset(response['offset'])\
        .limit(response['per_page'])
    response['data'] = [ person.toJson() for person in q ] 
    return response



##################################################
####           URLS: /activity/...
##################################################
def _activityquery_github():
    return Session.query(ActivityInGithub,Repo,Person)\
            .order_by(ActivityInGithub.timestamp.desc())\
            .filter(Repo.full_name==ActivityInGithub.repo)\
            .filter(Person.id==ActivityInGithub.user_id)
def _activitydict_github(act,repo,person):
    out = act.toJson()
    out['repo'] = repo.toJson()
    out['person'] = person.toJson()
    out['_activity_type'] = 'github'
    return out

def _activityquery_mailman():
    return Session.query(ActivityInMailman,Mailman,Person)\
            .order_by(ActivityInMailman.timestamp.desc())\
            .filter(Mailman.id==ActivityInMailman.mailman_id)\
            .filter(Person.email==ActivityInMailman.email)
def _activitydict_mailman(act,mailman,person):
    out = act.toJson()
    out['mailman'] = mailman.toJson()
    out['person'] = person.toJson()
    out['_activity_type'] = 'mailman'
    return out

def _activityquery_buddypress():
    return Session.query(ActivityInBuddypress,Person)\
            .order_by(ActivityInBuddypress.timestamp.desc())\
            .filter(Person.login==ActivityInBuddypress.login)
def _activitydict_buddypress(act,person):
    out = act.toJson()
    out['person'] = person.toJson()
    out['_activity_type'] = 'buddypress'
    return out
    
def _activityquery_twitter():
    return Session.query(Tweet,Person)\
            .order_by(Tweet.timestamp.desc())\
            .filter(Person.twitter==Tweet.screen_name)
def _activitydict_twitter(act,person):
    out = act.toJson()
    out['person'] = person.toJson()
    out['_activity_type'] = 'twitter'
    return out
    

@endpoint('/activity/twitter')
def activity__twitter():
    q = _activityquery_twitter()
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ _activitydict_twitter(x,y) for x,y in q ]
    return response

@endpoint('/activity/github')
def activity__github():
    select_repos = request.args.get('repo',None)
    q = _activityquery_github()
    if select_repos is not None:
        select_repos = select_repos.split(',')
        q = q.filter(Repo.full_name.in_(select_repos))
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ _activitydict_github(x,y,z) for x,y,z in q ]
    return response

@endpoint('/activity/mailman')
def activity__mailman():
    select_lists = request.args.get('list',None)
    q = _activityquery_mailman()
    if select_lists is not None:
        select_lists = select_lists.split(',') 
        q = q.filter(func.lower(Mailman.name).in_(select_lists))
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ _activitydict_mailman(x,y,z) for x,y,z in q ]
    return response



##################################################
####           URL: /stream/
##################################################
@endpoint('/stream')
def stream():
    # Facet by types
    types=['buddypress','github','twitter','mailman']
    _types = request.args.get('type',None)
    if _types is not None:
        _types = _types.split(',')
        types = list( set(types).intersection(set(_types)) )
    # Facet by login
    _login = request.args.get('login')
    filter_login = None
    if _login is not None:
        _login = _login.split(',')
        filter_login = Person.login.in_(_login)
    # Facet by opinion
    _opinion = request.args.get('opinion')
    filter_opinion = None
    if _opinion is not None:
        filter_opinion = Person._opinion==_opinion
    # Facet by timestamp range
    hours = int(request.args.get('hours', 0))
    days = int(request.args.get('days',0))
    if not days or hours:
        hours = 4
    # Page number 
    page = int(request.args.get('page',0))
    d = timedelta(hours=hours,days=days)
    timestamp_min = datetime.now() - d * (page+1)
    timestamp_max = timestamp_min + d
    filter_timestamp = lambda x: x.timestamp.between( timestamp_min, timestamp_max )
    results = []
    if 'github' in types:
        q = _activityquery_github().filter( filter_login ).filter( filter_opinion ).filter( filter_timestamp(ActivityInGithub) )
        results += [ _activitydict_github(x,y,z) for x,y,z in q ]
    if 'mailman' in types:
        q = _activityquery_mailman().filter( filter_login ).filter( filter_opinion ).filter( filter_timestamp(ActivityInMailman) )
        results += [ _activitydict_mailman(x,y,z) for x,y,z in q ]
    if 'buddypress' in types:
        q = _activityquery_buddypress().filter( filter_login ).filter( filter_opinion ).filter( filter_timestamp(ActivityInBuddypress) )
        results += [ _activitydict_buddypress(x,y) for x,y in q ]
    if 'twitter' in types:
        q = _activityquery_twitter().filter( filter_login ).filter( filter_opinion ).filter( filter_timestamp(Tweet) )
        results += [ _activitydict_twitter(x,y) for x,y in q ]
    results = sorted(results, key = lambda x : x['timestamp'],reverse=True)
    # Construct a results object 
    response = { 'ok': True }
    response['hours'] = hours
    response['days'] = days
    response['timestamp_min'] = timestamp_min.isoformat()
    response['timestamp_max'] = timestamp_max.isoformat()
    response['type'] = types
    response['page'] = page
    response['login'] = _login
    response['opinion'] = _opinion
    response['data'] = results
    next_args = dict(request.args.items() + [('page',page+1)])
    response['next'] = request.base_url + '?'+urlencode(next_args)
    return response


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
def history__github_all():
    grain = _get_grain()
    date_group = func.date_trunc(grain, SnapshotOfRepo.timestamp)
    num_repos = Session.query(Repo).count()
    # Execute the query
    fromobj = select([ date_group,\
                    SnapshotOfRepo.repo_id,\
                    func.max(SnapshotOfRepo.open_issues),\
                    func.max(SnapshotOfRepo.size),\
                    func.max(SnapshotOfRepo.watchers),\
                    func.max(SnapshotOfRepo.forks)])\
            .group_by(SnapshotOfRepo.repo_id)\
            .group_by(date_group)\
            .order_by(date_group.desc())\
            .limit(num_repos*12)\
            .alias('fromobj')
    # Hit the DB with one (quite complex) query to group by date & join on Repo
    q = Session.query(fromobj,Repo).filter(Repo.id==fromobj.c['repo_id'])
    results = {}
    _dictize = lambda x: {
        'timestamp':x[0].date().isoformat(),
        'open_issues':x[2],
        'size':x[3],
        'watchers':x[4],
        'forks':x[5],
    }
    for x in q:
        repo = x[6]
        n = repo.full_name
        if not n in results:
            results[n] = { 'repo' : repo.toJson(), 'data': [] }
        # Add a history entry
        results[n]['data'].append( _dictize(x) )
    # Inner function transforms SELECT tuple into recognizable format
    response = {'ok':True}
    response['grain'] = grain
    response['data'] = results
    return response


@endpoint('/history/github/<owner>/<reponame>')
def history__github(**args):
    reponame = args['owner']+'/'+args['reponame']
    repo = Session.query(Repo)\
            .filter(Repo.full_name==reponame)\
            .first()
    assert repo, 'repository "%s" does not exist' % reponame
    grain = _get_grain()
    date_group = func.date_trunc(grain, SnapshotOfRepo.timestamp)
    # Count the results
    response = _prepare(_count_group_by(date_group))
    # Execute the query
    stmt = select([ date_group,\
                    func.max(SnapshotOfRepo.open_issues),\
                    func.max(SnapshotOfRepo.size),\
                    func.max(SnapshotOfRepo.watchers),\
                    func.max(SnapshotOfRepo.forks)])\
            .group_by(date_group)\
            .where(SnapshotOfRepo.repo_id==repo.id)\
            .order_by(date_group.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    q = engine.execute(stmt)
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'timestamp':x[0].date().isoformat(),
        'open_issues':x[1],
        'size':x[2],
        'watchers':x[3],
        'forks':x[4],
    }
    response['data'] = [ _dictize(x) for x in q ] 
    response['grain'] = grain
    response['repo_id'] = repo.id
    response['repo_created_at'] = repo.created_at.isoformat()
    response['repo_description'] = repo.description
    response['repo_fork'] = repo.fork
    response['repo_full_name'] = repo.full_name
    response['repo_homepage'] = repo.homepage
    response['repo_html_url'] = repo.html_url
    response['repo_language'] = repo.language
    return response

@endpoint('/history/mailman')
def history__mailman_all():
    grain = _get_grain()
    date_group = func.date_trunc(grain, SnapshotOfMailman.timestamp)
    num_lists = Session.query(Mailman).count()
    # Execute the query
    fromobj = select([ date_group,\
                    SnapshotOfMailman.mailman_id,\
                    func.max(SnapshotOfMailman.posts_today),\
                    func.max(SnapshotOfMailman.subscribers)])\
            .group_by(SnapshotOfMailman.mailman_id)\
            .group_by(date_group)\
            .order_by(date_group.desc())\
            .limit(num_lists*12)\
            .alias('fromobj')
    # Hit the DB with one (quite complex) query to group by date & join on Repo
    q = Session.query(fromobj,Mailman).filter(Mailman.id==fromobj.c['mailman_id'])
    results = {}
    _dictize = lambda x: {
        'timestamp':x[0].date().isoformat(),
        'posts':x[2],
        'subscribers':x[3],
    }
    for x in q:
        mailman = x[4]
        n = mailman.name
        if not n in results:
            results[n] = { 'mailman' : mailman.toJson(), 'data': [] }
        # Add a history entry
        results[n]['data'].append( _dictize(x) )
    # Inner function transforms SELECT tuple into recognizable format
    response = {'ok':True}
    response['grain'] = grain
    response['data'] = results
    return response

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
    # Execute the query
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


@endpoint('/history/buddypress')
def history__buddypress():
    grain = _get_grain()
    date_group = func.date_trunc(grain, SnapshotOfBuddypress.timestamp)
    # Count the results
    response = _prepare(_count_group_by(date_group))
    # Execute the query
    stmt = select([ date_group,\
                    func.max(SnapshotOfBuddypress.num_users)])\
            .group_by(date_group)\
            .order_by(date_group.desc())\
            .offset(response['offset'])\
            .limit(response['per_page'])
    q = engine.execute(stmt)
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'timestamp':x[0].date().isoformat(),
        'num_users':x[1],
    }
    response['data'] = [ _dictize(x) for x in q ] 
    response['grain'] = grain
    return response


##################################################
####           URLS: /write/...
##################################################
def person_set_opinion():
    # TODO (securely) write__person
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

