#!/usr/bin/env python 

from dash import twitter
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Twitter activity into the database.')
    parser.add_argument('--since', default='', type=str, help='Download tweets since this tweet ID'),
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    twitter.scrape_tweets(since=arg.since,verbose=arg.verbose)

if __name__=='__main__':
    main()



