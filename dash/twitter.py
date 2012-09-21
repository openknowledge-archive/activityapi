import tweepy
import os
import re
from dash.backend import Session
from dash.backend.model import Tweet,Person,SnapshotOfTwitter,TwitterAccount,SnapshotOfTwitterAccount
from sqlalchemy import func
from datetime import datetime,timedelta

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


### daily snapshot_twitteraccounts mechanism
### Monitors follower stats for each twitteraccount
def scrape_twitteraccounts(verbose=False):
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

### daily snapshot_twitter mechanism
### Downloads all tweet data

def snapshot_twitter(verbose=False):
    """Create SnapshotOfTwitter objects in the database for 
       every day since the last time this was run."""
    today = datetime.now().date()
    until = today - timedelta(days=1)
    # By default, gather 45 days of snapshots
    since = until - timedelta(days=45)
    # Move 'since' forward if snapshots exist
    latest = Session.query(SnapshotOfTwitter)\
            .order_by(SnapshotOfTwitter.timestamp.desc())\
            .first()
    if latest:
        if latest.timestamp>=until:
            if verbose: print ' -> most recent snapshots have already been processed.'
            return
        since = latest.timestamp + timedelta(days=1)
    while since <= until:
        snapshot = _create_snapshot(since)
        if verbose: print '  -> ',snapshot.toJson()
        Session.add(snapshot)
        since += timedelta(days=1)
    Session.commit()

def _create_snapshot(day):
    # Grab all tweets that day
    q = Session.query(Tweet)\
            .filter( Tweet.timestamp.between(day,day+timedelta(days=1)) )
    tweets = list(q)
    tweets_today = len(tweets)
    # Grab a table of word -> frequency
    word_freq = _analyse_word_freq(q)
    hashtags = _extract_hashtags(word_freq)[:50]
    links = _extract_links(word_freq)[:50]
    words = _extract_words(word_freq)[:50]
    authors = _extract_authors(q)
    return SnapshotOfTwitter(day, tweets_today, hashtags, links, words, authors)

def _analyse_word_freq(query):
    freq = {}
    regex = re.compile(r'[\w:/#\.]+')
    for tweet in query:
        text = tweet.text
        for match in regex.finditer(tweet.text):
            # Case insensitive frequency count
            word = match.group(0).lower()
            freq[word] = freq.get(word,0) + 1
    return freq

def _extract_hashtags(word_freq):
    filtered = [ (key,value) for key,value in word_freq.items() if key[0]=='#' and value>1 ]
    ordered = sorted(filtered, key=lambda x:x[1], reverse=True)
    return [ {'hashtag':x[0], 'frequency':x[1]} for x in ordered ]

def _extract_links(word_freq):
    filtered = [ (key,value) for key,value in word_freq.items() if key[:5]=='http:' and value>1]
    ordered = sorted(filtered, key=lambda x:x[1], reverse=True)
    return [ {'link':x[0],'frequency':x[1]} for x in ordered ]

def _extract_words(word_freq, min_word_length=7):
    is_word = lambda x: len(x)>min_word_length \
            and not x[:5]=='http:'\
            and not x[0]=='#'
    filtered = [ (key,value) for key,value in word_freq.items() if is_word(key) and value>1 ]
    ordered = sorted(filtered, key=lambda x:x[1], reverse=True)
    return [ {'word':x[0], 'frequency':x[1]} for x in ordered ]

def _extract_authors(query, limit=20):
    """Who tweeted the most?"""
    freq = {}
    for tweet in query:
        author = tweet.screen_name
        freq[author] = freq.get(author,0) + 1
    # Grab top-ranked as tuples
    freqlist = sorted( freq.items(), key=lambda x:x[1])
    out = []
    while len(freqlist)>0 and len(out)<limit:
        x = freqlist.pop()
        author = _get_login_for(x[0])
        if author:
            out.append({'screen_name':x[0], 'frequency':x[1], 'login':author})
    return out

def _get_login_for(twitter_handle):
    q = Session.query(Person)\
            .filter(func.lower(Person.twitter)==func.lower(twitter_handle))\
            .first()
    if q:
        return q.login
    
