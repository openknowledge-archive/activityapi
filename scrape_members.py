#!/usr/bin/env python

import dash.scraper
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Import the latest members list into the DB.')
    parser.add_argument('url', type=str, help='URL of the JSON database dump'),
    arg = parser.parse_args()
    dash.scraper.scrape_members(arg.url)
