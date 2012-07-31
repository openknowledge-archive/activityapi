#!/usr/bin/env python 

import dash.twitter
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Update the tweets table')
    parser.add_argument('--since', default='', type=str, help='Download tweets since this tweet ID'),
    arg = parser.parse_args()
    dash.twitter.scrape_tweets(since=arg.since)



