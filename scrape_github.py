#!/usr/bin/env python

import dash.git
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Github for events and stats')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('--repo', action='store_true', dest='repo', help='(Daily) Scrape list of repositories from Github')
    parser.add_argument('--activity', action='store_true', dest='activity', help='(10 min) Scrape latest events & activity from Github')
    arg = parser.parse_args()
    if not arg.repo and not arg.activity:
        parser.print_usage()
        print 'Error: Script must be run with --activity or --repo'
        exit(-1)
    if arg.repo:
        if arg.verbose: print 'Fetching repository list from Github (slow)...'
        repos = dash.git.scrape_repos() 
        if arg.verbose: print 'Got %d repos. Writing to database...' % len(repos)
        dash.git.save_repos( repos )
    if arg.activity:
        dash.git.scrape_github(arg.verbose)

if __name__=='__main__':
    main()
