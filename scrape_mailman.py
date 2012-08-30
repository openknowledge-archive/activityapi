#!/usr/bin/env python

import dash.mailman
import argparse

def main():
    parser = argparse.ArgumentParser(description='Scrape Mailman for mailing list data')
    arg = parser.parse_args()
    dash.mailman.update_local( dash.mailman.scrape_remote() )

if __name__=='__main__':
    main()
