#!/usr/bin/env python 

from dash import twitter
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Twitter activity into the database.')
    parser.add_argument('--since', default='', type=str, help='Download tweets since this tweet ID'),
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('mode', choices=['daily','activity'], help='Scraper mode. Daily stats update or regular activity scraper.')
    arg = parser.parse_args()
    if arg.mode=='daily':
        twitter.snapshot_twitter(verbose=arg.verbose)
    elif arg.mode=='activity':
        twitter.scrape_tweets(since=arg.since,verbose=arg.verbose)

if __name__=='__main__':
    main()



