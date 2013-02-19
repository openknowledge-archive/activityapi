import tweepy
import os
import re
from dash.backend import Session
from dash.backend.model import TwitterAccount,SnapshotOfTwitterAccount
from sqlalchemy import func
from datetime import datetime,timedelta

def _connect():
    # Grab an authenticated instance of the tweepy API
    consumer_key = 'G9JTBcBgRWFGTPnjVsL9g'
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    access_token = '726428108-cIXizVVYrBGRhTnbxeXAHgA05VpkvtIGAqGEqT9a'
    access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    assert consumer_secret and access_token_secret, 'Set environment variables: "TWITTER_CONSUMER_SECRET" and "TWITTER_ACCESS_TOKEN_SECRET" to access the API. (https://dev.twitter.com/apps/2927379/oauth)'
    auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
    auth.set_access_token(access_token,access_token_secret)
    return tweepy.API(auth)

def scrape_twitteraccounts(verbose=False):
    """Monitors follower stats for each twitteraccount"""
    api = _connect()
    for ta in Session.query(TwitterAccount):
        if verbose: print 'Scraping %s...' % ta.screen_name
        u = api.get_user(ta.screen_name)
        ta.followers = u.followers_count
        ta.following = u.friends_count
        ta.tweets = u.statuses_count
        ta.name = u.name
        ta.description = u.description
        if verbose: print ta.toJson()
    Session.commit()

def snapshot_twitteraccounts(verbose=False):
    """Create today's SnapshotOfTwitterAccount"""
    today = datetime.now().date()
    for ta in Session.query(TwitterAccount):
        sn = SnapshotOfTwitterAccount(today, ta.screen_name, ta.followers, ta.following, ta.tweets)
        if verbose: print 'Snapshot created:',sn.toJson()
        Session.add(sn)
    Session.commit()

