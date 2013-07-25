#!/usr/bin/env python 

import argparse
import re
from lib.backend import Session
from lib.backend.model import SnapshotOfTwitterAccount
from sqlalchemy import func
from datetime import datetime,timedelta
import twitter
import os

def open_api():
    # Connect to a twitter account as configured in the environment
    api = twitter.Api(consumer_key=os.getenv('TWITTER_CONSUMER_KEY'),
                      consumer_secret=os.getenv('TWITTER_CONSUMER_SECRET'),
                      access_token_key=os.getenv('TWITTER_ACCESS_TOKEN'),
                      access_token_secret=os.getenv('TWITTER_ACCESS_SECRET'))
    api.VerifyCredentials()
    return api

def snapshot_twitteraccounts(verbose=False):
    """Create today's SnapshotOfTwitterAccounts"""
    api = open_api()
    friends = api.GetFriends()

    for friend in friends:
        if verbose: print 'Scraping %s...' % friend.screen_name
        screen_name = friend.screen_name.lower()
        if screen_name=='theannotator':
            # legacy reasons
            screen_name = 'TheAnnotator'
        followers = friend.followers_count
        following = friend.friends_count
        tweets = friend.statuses_count
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

