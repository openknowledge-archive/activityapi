from pprint import pprint
import sqlite3 as lite
import requests
import json

def connect_db(filename):
    assert file(filename)
    return lite.connect( filename )

def scrape_tweets( con, endpoint, username, since_id='' ):
    payload = { 'q' : 'from:%s'%username }
    if since_id:
        payload['since_id'] = since_id
    r = requests.get( endpoint, params=payload )

    print r.url
    assert r.status_code==200
    obj = json.loads( r.content )
    print 'Got %d tweets from %s' % ( len(obj['results']), username )
    cur = con.cursor()
    for tweet in obj['results']:
        query = "insert into tw values('%s','%s','%s','%s')"
        query %= (  tweet['from_user'],
                    tweet['id_str'],
                    tweet['created_at'],
                    tweet['text'])
        print query
        cur.execute( query )

if __name__=='__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Download tweets from the given user into the database')
    parser.add_argument('endpoint', type=str, help='Twitter search endpoint'),
    parser.add_argument('user', type=str, help='Twitter Username'),
    parser.add_argument('--since', default='', type=str, help='Download tweets since this tweet ID'),
    parser.add_argument('--db', default='database.sqlite', type=str, help='Location of SQLite database'),
    arg = parser.parse_args()
    with connect_db(arg.db) as con:
        scrape_tweets(con, arg.endpoint, arg.user, arg.since)
