from lib.frontend import app
from lib.backend import Session
from lib.backend.model import *
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
    q = Session.query(SnapshotOfMailman.list_name).distinct()
    response['data'] = [ x[0] for x in q ]
    response['total'] = q.count()
    return response
##################################################
####           URLS: /activity/...
##################################################
@endpoint('/activity/mailman')
def activity__mailman():
    select_lists = request.args.get('list',None)
    q = Session.query(ActivityInMailman)\
            .order_by(ActivityInMailman.timestamp.desc())
    if select_lists is not None:
        select_lists = select_lists.split(',') 
        q = q.filter(func.lower(ActivityInMailman.list_name).in_(select_lists))
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ x.toJson() for x in q ]
    return response


##################################################
####           URLS: /history/...
##################################################
@endpoint('/history/twitter')
def history__twitter():
    grain = _get_grain()
    accountnames = request.args.get('name',None)
    # Filter by account name
    accountFilter = None
    if accountnames is not None:
        accountnames = accountnames.split(',')
        accountFilter = SnapshotOfTwitterAccount.screen_name.in_(accountnames)
    # Query: Range of dates
    date_group = func.date_trunc(grain, SnapshotOfTwitterAccount.timestamp)
    q1 = Session.query()\
            .add_column( func.distinct(date_group).label('d') )\
            .order_by(date_group.desc())
    response = _prepare(q1.count())
    q1 = q1.offset( response['offset'] )\
            .limit( response['per_page'] )
    if q1.count():
        date_column = q1.subquery().columns.d
        (min_date,max_date) = Session.query(func.min(date_column), func.max(date_column)).first()
    else:
        # Impossible date range
        (min_date,max_date) = datetime.now()+timedelta(days=1),datetime.now()
    # Grouped query
    S = SnapshotOfTwitterAccount
    q = Session.query()\
            .add_column( func.max(S.followers) )\
            .add_column( func.max(S.following) )\
            .add_column( func.max(S.tweets) )\
            .add_column( date_group )\
            .add_column( S.screen_name )\
            .group_by(date_group)\
            .group_by(S.screen_name)\
            .order_by(date_group.desc())\
            .filter( date_group>=min_date )\
            .filter( date_group<=max_date )\
            .filter( accountFilter )
    results = {}
    _dictize = lambda x: {
        'followers':x[0],
        'following':x[1],
        'tweets':x[2],
        'timestamp':x[3].date().isoformat(),
        'screen_name':x[4]
    }
    for x in q:
        x = _dictize(x)
        name = x['screen_name']
        if not (name in results):
            latest = Session.query(S).order_by(S.timestamp.desc()).first()
            results[name] = { 
                    'account':{
                        'screen_name':name,
                        'followers':latest.followers,
                        'following':latest.following,
                        'tweets':latest.tweets,
                    },
                    'data':[] 
            }
        results[name]['data'].append(x)
    response['data'] = results
    response['grain'] = grain
    return response

@endpoint('/history/github')
def history__github():
    grain = _get_grain()
    # Map of github entries
    github = { x.id : x for x in Session.query(Repo) }
    # Filtered list of github IDs
    repo = request.args.get('repo', None)
    repoFilter = None
    if repo is not None:
        repo = repo.split(',')
        ids = []
        for name in repo:
            m = filter(lambda x:x.full_name==name, github.values())
            assert m,'Repository %s does not exist' % name
            ids.append(m[0].id)
        repoFilter = SnapshotOfRepo.repo_id.in_(ids)
    # Date filter
    date_group = func.date_trunc(grain, SnapshotOfRepo.timestamp)
    # Query: Range of dates
    q1 = Session.query()\
            .add_column( func.distinct(date_group).label('d') )\
            .order_by(date_group.desc())
    response = _prepare(q1.count())
    q1 = q1.offset( response['offset'] )\
            .limit( response['per_page'] )
    if q1.count():
        date_column = q1.subquery().columns.d
        (min_date,max_date) = Session.query(func.min(date_column), func.max(date_column)).first()
    else:
        # Impossible date range
        (min_date,max_date) = datetime.now()+timedelta(days=1),datetime.now()
    # Grouped query
    S = SnapshotOfRepo
    q = Session.query()\
            .add_column( func.sum(S.watchers) )\
            .add_column( func.max(S.forks) )\
            .add_column( func.max(S.open_issues) )\
            .add_column( func.max(S.size) )\
            .add_column( date_group )\
            .add_column( S.repo_id )\
            .group_by(date_group)\
            .group_by(S.repo_id)\
            .order_by(date_group.desc())\
            .filter( date_group>=min_date )\
            .filter( date_group<=max_date )\
            .filter( repoFilter )
    results = {}
    _dictize = lambda x: {
        'watchers':x[0],
        'forks':x[1],
        'issues':x[2],
        'size':x[3],
        'timestamp':x[4].date().isoformat(),
    }
    for x in q:
        r = github[ x[5] ]
        results[r.full_name] = results.get(r.full_name, { 'repo':r.toJson(), 'data':[] })
        results[r.full_name]['data'].append( _dictize(x) )
    # Inner function transforms SELECT tuple into recognizable format
    response['grain'] = grain
    response['data'] = results
    response['repos'] = repo
    response['min_date'] = min_date.date().isoformat()
    response['max_date'] = max_date.date().isoformat()
    return response


@endpoint('/history/facebook')
def history__facebook():
    grain = _get_grain()
    # Date filter
    date_group = func.date_trunc(grain, SnapshotOfFacebook.timestamp)
    # Grouped query
    S = SnapshotOfFacebook
    q = Session.query()\
            .add_column( date_group )\
            .add_column( func.max(S.likes) )\
            .group_by(date_group)\
            .order_by(date_group.desc())
    response = _prepare(q.count())
    q = q.offset( response['offset'] )\
          .limit( response['per_page'] )
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'timestamp':x[0].isoformat(),
        'likes':x[1]
    }
    results = {
            'history': [ _dictize(x) for x in q ],
            'likes' : Session.query(S).order_by(S.timestamp.desc()).first().likes
            }
    # Write response
    response['grain'] = grain
    response['data'] = results
    return response


@endpoint('/history/mailman')
def history__mailman():
    grain = _get_grain()
    # Filtered list of mailman IDs
    lists = request.args.get('list')
    listFilter = None
    if lists is not None:
        lists = lists.split(',')
        listFilter = func.lower(SnapshotOfMailman.list_name).in_(lists)
    # Date filter
    date_group = func.date_trunc(grain, SnapshotOfMailman.timestamp)
    # Query: Range of dates
    q1 = Session.query()\
            .add_column( func.distinct(date_group).label('d') )\
            .order_by(date_group.desc())
    response = _prepare(q1.count())
    q1 = q1.offset( response['offset'] )\
            .limit( response['per_page'] )
    if q1.count():
        subquery = q1.subquery()
        (min_date,max_date) = Session.query(func.min(subquery.columns.d), func.max(subquery.columns.d)).first()
    else:
        # Impossible date range
        (min_date,max_date) = datetime.now()+timedelta(days=1),datetime.now()
    # Grouped query
    S = SnapshotOfMailman
    q = Session.query()\
            .add_column( func.sum(S.posts_today) )\
            .add_column( func.max(S.subscribers) )\
            .add_column( date_group )\
            .add_column( S.list_name )\
            .group_by(date_group)\
            .group_by(S.list_name)\
            .order_by(date_group.desc())\
            .filter( date_group>=min_date )\
            .filter( date_group<=max_date )\
            .filter( listFilter )
    results = {}
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'posts':x[0],
        'subscribers':x[1],
        'timestamp':x[2].isoformat(),
    }
    # Build output datastructure from rows
    for x in q:
        list_name = x[3]
        results[list_name] = results.get(list_name, { 'list_name':list_name, 'data':[] })
        results[list_name]['data'].append( _dictize(x) )
    # Write response
    response['grain'] = grain
    response['data'] = results
    response['list'] = lists
    response['min_date'] = min_date.isoformat()
    response['max_date'] = max_date.isoformat()
    return response


@endpoint('/history/mailchimp')
def history__mailchimp():
    grain = _get_grain()
    # Filtered list of mailchimp names
    lists = request.args.get('list')
    listFilter = None
    if lists is not None:
        lists = lists.split(',')
        listFilter = SnapshotOfMailchimp.name.in_(lists)
    # Date filter
    date_group = func.date_trunc(grain, SnapshotOfMailchimp.timestamp)
    # Query: Range of dates
    q1 = Session.query()\
            .add_column( func.distinct(date_group).label('d') )\
            .order_by(date_group.desc())
    response = _prepare(q1.count())
    q1 = q1.offset( response['offset'] )\
            .limit( response['per_page'] )
    if q1.count():
        subquery = q1.subquery()
        (min_date,max_date) = Session.query(func.min(subquery.columns.d), func.max(subquery.columns.d)).first()
    else:
        # Impossible date range
        (min_date,max_date) = datetime.now()+timedelta(days=1),datetime.now()
    # Grouped query
    S = SnapshotOfMailchimp
    q = Session.query()\
            .add_column( func.max(S.members) )\
            .add_column( date_group )\
            .add_column( S.name )\
            .group_by(date_group)\
            .group_by(S.name)\
            .order_by(date_group.desc())\
            .filter( date_group>=min_date )\
            .filter( date_group<=max_date )\
            .filter( listFilter )
    results = {}
    # Inner function transforms SELECT tuple into recognizable format
    _dictize = lambda x: {
        'members':x[0],
        'timestamp':x[1].isoformat(),
    }
    # Build output datastructure from rows
    for x in q:
        name = x[2]
        results[name] = results.get(name, { 'name':name, 'data':[] })
        results[name]['data'].append( _dictize(x) )
        results[name]['members'] = Session.query(S).filter(S.name==name).order_by(S.timestamp.desc()).first().members
    # Write response
    response['grain'] = grain
    response['data'] = results
    response['list'] = lists
    response['min_date'] = min_date.isoformat()
    response['max_date'] = max_date.isoformat()
    return response



##################################################
####           URLS: /debug/...
##################################################

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

