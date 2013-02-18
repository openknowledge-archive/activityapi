#!/usr/bin/env python

import argparse

from dash import mailchimp

def main():
    parser = argparse.ArgumentParser(description='Scrape Mailchimp for daily stats.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    mailchimp.snapshot_mailchimp( verbose=arg.verbose )

if __name__=='__main__':
    main()
