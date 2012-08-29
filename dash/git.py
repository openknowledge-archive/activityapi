from github import Github
from dash.backend import Session
from dash.backend.model import Person, EventGithub

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






