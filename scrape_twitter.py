#!/usr/bin/env python 

import dash.scraper
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Download tweets from the given user into the database')
    parser.add_argument('url', type=str, help='Twitter API url endpoint'),
    parser.add_argument('user', type=str, help='Twitter Username'),
    parser.add_argument('--since', default='', type=str, help='Download tweets since this tweet ID'),
    parser.add_argument('--commit', action='store_true', help='To commit to the database'),
    arg = parser.parse_args()
    dash.scraper.scrape_tweets(arg.url, arg.user, since_id=arg.since, commit=arg.commit)
