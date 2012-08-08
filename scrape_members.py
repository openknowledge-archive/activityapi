#!/usr/bin/env python

import dash.buddypress
import argparse

if __name__=='__main__':
    # NOT READY FOR PRODUCTION
    parser = argparse.ArgumentParser(description='Import the latest members list into the DB.')
    parser.add_argument('url', type=str, help='URL of the JSON database dump'),
    arg = parser.parse_args()
    dash.buddypress.scrape_database(arg.url)
