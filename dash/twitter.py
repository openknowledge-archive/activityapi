import tweepy
import os
from dash.backend import Session
from dash.backend.model import Tweet
from sqlalchemy import func

# The user "z_cron" maintains a set of private twitter lists
# in order to silently track everybody without murdering the API.
# Lists are limited to 500 users, so a partition scheme is used.
LISTS = [
    'okfn_0_9',
    'okfn_a_d',
    'okfn_e_j',
    'okfn_k_r',
    'okfn_s_z'
]

def scrape_tweets(since='',verbose=False):
    from sys import stderr
    if verbose: print 'Connecting to Twitter...'
    api = _connect()
    if not since:
        q = Session.query( func.max(Tweet.tweet_id) )
        since = q.first()[0]
        if not since:
            raise ValueError('No tweets exist in the database. Which tweet_id should I start from?')
        if verbose: print 'Last known tweet_id=%d' % since
    if verbose: 'Fetching user lists from Twitter...'
    lists = { x.name : x for x in api.lists() }
    assert all( [lists[x] for x in LISTS] )
    # Poll each list and flush it to the database
    full_count = 0
    for x in LISTS:
        try:
            if verbose: print 'Polling list %s...' % x
            sub_count = 0
            for raw in _scrape_api(api, lists[x], since):
                try:
                    t = Tweet.parse(raw)
                except Exception as e:
                    print >>stderr, 'Exception while parsing tweet %s: %s' % (raw_tweet.id, str(e))
                else:
                    Session.add(t)
                    sub_count += 1
                    full_count += 1
            if verbose: print '  -> List yielded %d tweets' % sub_count
        except Exception as e:
            print >>stderr, 'Exception while polling %s: %s' % (x, str(e))
    Session.commit()
    if verbose: print '=> Got %d tweets total' % full_count

def _scrape_api(api,lst,since):
    """Grab hold of the twitter firehose for a given list"""
    c = tweepy.Cursor(api.list_timeline,lst.user.screen_name,lst.slug,since_id=since)
    return c.items()

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

