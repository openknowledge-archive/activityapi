#!/usr/bin/env python

import dash.mailman
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Mailman for mailing list data')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    dash.mailman.save_mailinglists( dash.mailman.scrape_mailinglists(arg.verbose), arg.verbose )

if __name__=='__main__':
    main()
