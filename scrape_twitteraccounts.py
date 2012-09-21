#!/usr/bin/env python 

from dash import twitter
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Twitter account information into the database.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('mode', choices=['daily','update'], help='Scraper mode. Update latest follower(etc) stats, or take daily snapshot')
    arg = parser.parse_args()
    if arg.mode=='daily':
        twitter.snapshot_twitteraccounts(verbose=arg.verbose)
    elif arg.mode=='update':
        twitter.scrape_twitteraccounts(verbose=arg.verbose)

if __name__=='__main__':
    main()

