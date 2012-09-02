#!/usr/bin/env python

from dash import mailman
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Mailman for list data and recent activity.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('mode', choices=['daily','activity'], help='Scraper mode. Daily stats update or regular activity scraper.')
    arg = parser.parse_args()
    if arg.mode=='daily':
        mailman_all = mailman.scrape_mailman( verbose=arg.verbose )
        mailman.save_mailman( mailman_all, verbose=arg.verbose )
        mailman.snapshot_mailman(verbose=arg.verbose)
    elif arg.mode=='activity':
        mailman.scrape_activity( verbose=arg.verbose )

if __name__=='__main__':
    main()
