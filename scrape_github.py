#!/usr/bin/env python

from lib import git
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Github for events and stats')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('mode', choices=['daily','activity'], help='Scraper mode. Daily stats update or regular activity scraper.')
    arg = parser.parse_args()
    if arg.mode=='daily':
        repos = git.scrape_repos(verbose=arg.verbose) 
        git.save_repos(repos, verbose=arg.verbose)
        git.snapshot_repos(repos, verbose=arg.verbose)
    elif arg.mode=='activity':
        git.scrape_github_activity(verbose=arg.verbose)

if __name__=='__main__':
    main()
