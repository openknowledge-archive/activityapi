#!/usr/bin/env python 

import dash.twitter
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Update the tweets table')
    arg = parser.parse_args()
    dash.twitter.scrape_tweets()
