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

def which_list(username):
    """Look up which partitioned list is used to monitor this user"""
    l = username[0] 
    if l<'0': raise ValueError(l)
    if l<='_': return LISTS[0]
    if l<='d': return LISTS[1]
    if l<='j': return LISTS[2]
    if l<='r': return LISTS[3]
    if l<='z': return LISTS[4]
    raise ValueError(l)

def add_all(names,lists):
    for x in names:
        try:
            lists[which_list(x)].add_member(x)
            print 'done:',x
        except tweepy.error.TweepError:
            print 'failed to add',x

def get_api():
    # Grab an authenticated instance of the tweepy API
    consumer_key = 'G9JTBcBgRWFGTPnjVsL9g'
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    access_token = '726428108-cIXizVVYrBGRhTnbxeXAHgA05VpkvtIGAqGEqT9a'
    access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    assert consumer_secret and access_token_secret, 'Set environment variables: "TWITTER_CONSUMER_SECRET" and "TWITTER_ACCESS_TOKEN_SECRET" to access the API. (https://dev.twitter.com/apps/2927379/oauth)'
    auth = tweepy.OAuthHandler(consumer_key,consumer_secret)
    auth.set_access_token(access_token,access_token_secret)
    return tweepy.API(auth)

def all_members(api,lst):
    """Which users are in this list?"""
    c = tweepy.Cursor(api.list_members,lst.user.screen_name,lst.slug)
    return [x for x in c.items()]

def all_tweets_since(api,lst,since):
    """Grab hold of the twitter firehose for a given list"""
    c = tweepy.Cursor(api.list_timeline,lst.user.screen_name,lst.slug,since_id=since)
    return c.items()

def scrape_tweets(since=''):
    api = get_api()
    if not since:
        q = Session.query( func.max(Tweet.tweet_id) )
        since = q.first()[0]
        if not since:
            raise ValueError('No tweets exist in the database. Which tweet_id should I start from?')
        print 'Last known tweet_id:',since
    lists = { x.name : x for x in api.lists() }
    assert all( [lists[x] for x in LISTS] )
    # Poll each list and flush it to the database
    full_count = 0
    for x in LISTS:
        try:
            print 'Polling list %s...' % x
            tweets = all_tweets_since( api, lists[x], since )
            sub_count = 0
            for raw_tweet in tweets:
                try:
                    t = Tweet.parse(raw_tweet)
                    Session.add(t)
                    sub_count += 1
                    full_count += 1
                except Exception as e:
                    print 'Exception while parsing tweet %s: %s' % (raw_tweet.id, str(e))
            Session.commit()
            print '  -> List yielded %d tweets' % sub_count
        except Exception as e:
            print 'Exception while polling %s: %s' % (x, str(e))
    print '=> Got %d tweets total' % full_count


