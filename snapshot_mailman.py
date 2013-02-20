#!/usr/bin/env python

import argparse
from lxml import html
import requests
import os
from lib import util
from lib.backend import Session
from lib.backend.model import SnapshotOfMailman, ActivityInMailman
from datetime import datetime,timedelta

def snapshot_mailman(verbose=False):
    lists = util.list_mailman_lists(verbose)
    today = datetime.now().date()
    for l in lists:
        if verbose: print 'Processing snapshots for %s...' % l['name']
        latest = Session.query(SnapshotOfMailman)\
                .filter(SnapshotOfMailman.list_name==l['name'])\
                .order_by(SnapshotOfMailman.timestamp.desc())\
                .first()
        # By default, gather 30 days of snapshots
        since = today - timedelta(days=180)
        if latest:
            if latest.timestamp>=today:
                if verbose: print ' -> most recent snapshots have already been processed.'
                continue
            since = latest.timestamp + timedelta(days=1)
        # Download subscriber list
        roster_url = l['link'].replace('listinfo','roster')
        num_subscribers = len(_scrape_subscribers(roster_url, verbose=verbose))
        # Create a snapshot of each day
        while since<today:
            posts_today = Session.query(ActivityInMailman)\
                            .filter(ActivityInMailman.list_name==l['name'])\
                            .filter(ActivityInMailman.timestamp.between(since,since+timedelta(days=1)))\
                            .count()
            sn = SnapshotOfMailman(\
                    list_name=l['name'],\
                    timestamp=since,\
                    subscribers=num_subscribers,
                    posts_today=posts_today)
            Session.add(sn)
            if verbose: print '  -> ',sn.toJson()
            since += timedelta(days=1)
        # Walk through message history, counting messages per day
        Session.commit()

def _scrape_subscribers(url, verbose=False):
    """Access the list's roster and generate 
       a text->href list of members of this list."""
    # admin@okfn.org can access list rosters
    payload={'roster-email':'admin@okfn.org', 'roster-pw':os.environ.get('MAILMAN_ADMIN_PW')}
    if verbose: print 'Scraping subscriber list for %s...' % url
    r = requests.post(url, data=payload)
    # Did we get in?
    if 'roster authentication failed' in r.text:
        raise ValueError('Roster authentication failed. Bad password.')
    # Scrape all the links to email--at--domain.com
    tree = html.fromstring( r.text )
    _links = tree.cssselect('a')
    links = filter( lambda x: '--at--' in x.attrib['href'], _links )
    return { x.text_content : x.attrib['href'] for x in links }
    

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Daily snapshot of Mailman activity.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_mailman(verbose=arg.verbose)
