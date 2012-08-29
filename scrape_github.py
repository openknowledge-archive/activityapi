#!/usr/bin/env python

import dash.git
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Github for events and stats')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    dash.git.scrape_github(arg.verbose)

if __name__=='__main__':
    main()
