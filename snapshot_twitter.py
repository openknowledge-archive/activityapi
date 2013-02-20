#!/usr/bin/env python 

import argparse
import tweepy
import os
import re
from lib.backend import Session
from lib.backend.model import SnapshotOfTwitterAccount
from sqlalchemy import func
from datetime import datetime,timedelta

TRACKED_ACCOUNTS =[
    'lod2project',
    'openspending',
    'reclinejs',
    'okfestival',
    'okfn',
    'okfnlabs',
    'ckanproject',
    'schoolofdata',
    'TheAnnotator'
    ]

def snapshot_twitteraccounts(verbose=False):
    """Create today's SnapshotOfTwitterAccounts"""
    api = tweepy.API()
    for screen_name in TRACKED_ACCOUNTS:
        if verbose: print 'Scraping %s...' % screen_name
        u = api.get_user(screen_name)
        followers = u.followers_count
        following = u.friends_count
        tweets = u.statuses_count
        today = datetime.now().date()
        # How long since we scraped this account?
        latest = Session.query(SnapshotOfTwitterAccount)\
                .filter(SnapshotOfTwitterAccount.screen_name==screen_name)\
                .order_by(SnapshotOfTwitterAccount.timestamp.desc())\
                .first()
        if latest and latest.timestamp>=today:
            if verbose: print ' -> most recent snapshot for %s has already been processed.' % screen_name
            continue
        # Create a snapshot 
        sn = SnapshotOfTwitterAccount(\
                timestamp=today,\
                screen_name=screen_name,\
                followers=followers,\
                following=following,\
                tweets=tweets)
        Session.add(sn)
        if verbose: print '  -> ',sn.toJson()
    Session.commit()

def main():
    parser = argparse.ArgumentParser(description='Scrape Twitter account information into the database.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_twitteraccounts(verbose=arg.verbose)

if __name__=='__main__':
    main()

