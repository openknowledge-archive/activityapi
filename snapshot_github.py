#!/usr/bin/env python

import argparse
from github import Github
from lib.backend import Session
from lib.backend.model import Repo, SnapshotOfRepo, Person, ActivityInGithub
from datetime import datetime,timedelta

def _get_repo_list(verbose=False):
    if verbose: print 'Connecting to GitHub...'
    gh = Github()
    if verbose: print 'Fetching profile for "okfn"...'
    okfn = gh.get_organization('okfn')
    if verbose: print 'Scraping repository list (slow)...'
    out = { x.full_name : x for x in okfn.get_repos() }
    if verbose: print 'Got %d repos.' % len(out)
    assert len(out) > 0, 'Wont proceed without receiving some repos from server.'
    return out

def snapshot_repos(verbose=False):
    """Create SnapshotOfRepo objects in the database for 
       every day since the last time this was run."""
    repo_list = _get_repo_list(verbose)
    day = timedelta(days=1)
    today = datetime.now().date()
    until = today - day
    for (repo_name,repo) in repo_list:
        if verbose: print 'Processing snapshots for %s...' % r.repo
        latest = Session.query(SnapshotOfRepo)\
                .filter(SnapshotOfRepo.repo_name==r.id)\
                .order_by(SnapshotOfRepo.timestamp.desc())\
                .first()
        # By default, gather 30 days of snapshots
        since = until - timedelta(days=30)
        if latest:
            if latest.timestamp>=until:
                if verbose: print ' -> most recent snapshots have already been processed.'
                continue
            since = latest.timestamp + day
        # as we have not deleted repos that no longer exist (see TODO above)
        # we have to check whether this repo still actually exists
        if not r.full_name in gh_repos:
            if verbose: print 'Skipping repo as no longer exists ' + r.full_name
            continue
        # Snapshot date for the last day (or more)
        gh_repo = gh_repos[ r.full_name ]
        while since <= until:
            snapshot = SnapshotOfRepo( since, r.id, gh_repo.open_issues, gh_repo.size, gh_repo.watchers, gh_repo.forks )
            if verbose: print '  -> ',snapshot.toJson()
            Session.add(snapshot)
            since += timedelta(days=1)
        Session.commit()


# Activity scrapers

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
    snapshot_repos(verbose=arg.verbose)
