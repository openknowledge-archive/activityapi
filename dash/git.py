from github import Github
from dash.backend import Session
from dash.backend.model import Repo, SnapshotOfRepo, Person, EventGithub
from datetime import datetime

def scrape_repos():
    gh = Github()
    okfn = gh.get_organization('okfn')
    # Slow, paginated server call:
    return { x.full_name : {'gh_repo':x} for x in okfn.get_repos() }

def save_repos( gh_repos ):
    """Update the 'repo' table"""
    # Add and update
    for k,v in gh_repos.items():
        # v is a dict of a 'repo' (from our ORM) and a 'gh_repo' (from the library)
        v['repo'] = Session.query(Repo).filter(Repo.full_name==k).first()
        if v['repo']:
            v['repo'].update(v['gh_repo'])
        else:
            v['repo'] = Repo(v['gh_repo'])
            Session.add( v['repo'] )
    # Delete
    for repo in Session.query(Repo):
        if not repo.full_name in gh_repos:
            Session.delete(repo)
    # Commit now to ensure repo.id is auto-assigned
    Session.commit()
    # Snapshot
    now = datetime.now()
    for k,v in gh_repos.items():
        repo_id = v['repo'].id
        snapshot = SnapshotOfRepo( now, repo_id, v['gh_repo'] )
        Session.add(snapshot)
    Session.commit()


# Activity scrapers

def scrape_github(verbose=False):
    q = Session.query(Person).filter(Person.github!=None)
    gh = Github()
    for x in q:
        if verbose: print 'Scraping events for %s (%s)...' % (x.display_name,x.login)
        gh_user = gh.get_user(x.github)
        _scrape_user_events( x.id, gh_user, verbose )
    Session.commit()
  
def _scrape_user_events( user_id, gh_user, verbose=False ):
    max = 30
    _latest = Session.query(EventGithub).filter(EventGithub.user_id==user_id).order_by(EventGithub.id.desc()).first()
    latest = _latest.id if _latest else 0
    if verbose: print '  latest=%d' % latest
    for x in gh_user.get_events():
        if max <= 0:
            if verbose: print '  scraped 30 events.'
            break
        if int(x.id) <= latest:
            if verbose: print '  scraped %d events. (no further events available)'%(30-max)
            break
        if verbose: print '  > type=%s  id=%s' % (x.type,x.id)
        Session.add( EventGithub(user_id, x) )
        max -= 1

