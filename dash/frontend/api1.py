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
    if per_page<0:
        # Unpaginated mode
        return response
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
    response = _prepare(per_page=-1)
    q = Session.query(Repo).order_by(Repo.full_name)
    response['data'] = [ x.toJson() for x in q ]
    response['total'] = q.count()
    return response

@endpoint('/data/mailman')
def data__mailman():
    """Unpaginated -- there are less than 200 entries in the database"""
    response = _prepare(per_page=-1)
    q = Session.query(Mailman).order_by(Mailman.name)
    response['data'] = [ x.toJson() for x in q ]
    response['total'] = q.count()
    return response

@endpoint('/data/person')
def data__person():
    opinion = request.args.get('opinion',None)
    q = Session.query(Person).order_by(Person.user_id.desc())
    if opinion is not None:
        if opinion=='': opinion = None
        q = q.filter(Person._opinion==opinion)
    response = _prepare(q.count())
    q = q.offset(response['offset'])\
        .limit(response['per_page'])
    response['data'] = [ person.toJson() for person in q ] 
    return response



##################################################
####           URLS: /activity/...
##################################################
@endpoint('/activity/person')
def activity__person():
    # TODO
    # Return any activity for all people
    #   ?login=zephod,rgrp
    #   >    Return activity for the selected users
    #   ?type=buddypress,github,twitter,mailman
    #   >    Return activity only of the specified types
    pass

@endpoint('/activity/twitter')
def activity__twitter():
    q = Session.query(Tweet).order_by(Tweet.tweet_id.desc())
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    response['data'] = [ x.toJson() for x in q ]
    return response

@endpoint('/activity/github')
def activity__github():
    select_repos = request.args.get('repo',None)
    q = Session.query(ActivityInGithub,Repo,Person)\
            .order_by(ActivityInGithub.timestamp.desc())\
            .filter(Repo.full_name==ActivityInGithub.repo)\
            .filter(Person.id==ActivityInGithub.user_id)
    if select_repos is not None:
        select_repos = [ 'okfn/'+x for x in select_repos.split(',') ]
        q = q.filter(Repo.full_name.in_(select_repos))
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    def _dictize(act,repo,person):
        out = act.toJson()
        out['repo'] = repo.toJson()
        out['person'] = person.toJson()
        return out
    response['data'] = [ _dictize(x,y,z) for x,y,z in q ]

    return response

@endpoint('/activity/mailman')
def activity__mailman():
    select_lists = request.args.get('list',None)
    q = Session.query(ActivityInMailman,Mailman,Person)\
            .order_by(ActivityInMailman.timestamp.desc())\
            .filter(Mailman.id==ActivityInMailman.mailman_id)\
            .filter(Person.email==ActivityInMailman.email)
    if select_lists is not None:
        select_lists = select_lists.split(',') 
        q = q.filter(func.lower(Mailman.name).in_(select_lists))
    response = _prepare( q.count() )
    q = q.offset(response['offset'])\
            .limit(response['per_page'])
    def _dictize(act,mailman,person):
        out = act.toJson()
        out['mailman'] = mailman.toJson()
        out['person'] = person.toJson()
        return out
    response['data'] = [ _dictize(x,y,z) for x,y,z in q ]

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
    # TODO implement
    assert False, 'All-repo history not yet implemented.'

@endpoint('/history/github/<reponame>')
def history__github(**args):
    repo = Session.query(Repo)\
            .filter(Repo.full_name=='okfn/'+args['reponame'])\
            .first()
    assert repo, 'repository "%s" does not exist' % args['reponame']
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
def history__mailman_all(**args):
    # TODO implement
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
def history__buddypress(**args):
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

