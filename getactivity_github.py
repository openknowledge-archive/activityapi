#!/usr/bin/env python

import argparse
from github import Github
from lib.backend import Session
from lib.backend.model import Person, ActivityInGithub
from datetime import datetime,timedelta

def scrape_github_activity(verbose=False):
    from sys import stderr
    q = Session.query(Person).filter(Person.github!=None)
    gh = Github()
    for x in q:
        if verbose: print 'Scraping events for %s (%s)...' % (x.display_name,x.login)
        try:
            gh_user = gh.get_user(x.github)
            _scrape_user_events( x.id, gh_user, verbose )
        except Exception as e:
            print >>stderr,'Exception processing github user %s' % x.login, e
    Session.commit()
  
def _scrape_user_events( user_id, gh_user, verbose=False ):
    max = 30
    _latest = Session.query(ActivityInGithub).filter(ActivityInGithub.user_id==user_id).order_by(ActivityInGithub.id.desc()).first()
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
        Session.add( ActivityInGithub(user_id, x) )
        max -= 1

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape Github for events and stats')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    scrape_github_activity(verbose=arg.verbose)
