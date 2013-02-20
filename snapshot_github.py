#!/usr/bin/env python

import argparse
from github import Github
from lib.backend import Session
from lib.backend.model import SnapshotOfGithub
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
    today = datetime.now().date()
    for (repo_name,repo) in repo_list.items():
        if verbose: print 'Processing snapshots for %s...' % repo_name
        latest = Session.query(SnapshotOfGithub)\
                .filter(SnapshotOfGithub.repo_name==repo_name)\
                .order_by(SnapshotOfGithub.timestamp.desc())\
                .first()
        # By default, gather 30 days of snapshots
        if latest and latest.timestamp>=today:
            if verbose: print ' -> most recent snapshots have already been processed.'
            continue
        # Snapshot date for the last day (or more)
        snapshot = SnapshotOfGithub( timestamp=today, repo_name=repo_name, open_issues=repo.open_issues, size=repo.size, watchers=repo.watchers, forks=repo.forks )
        if verbose: print '  -> ',snapshot.toJson()
        Session.add(snapshot)
        Session.commit()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape Github for events and stats')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_repos(verbose=arg.verbose)
