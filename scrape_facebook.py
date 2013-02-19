#!/usr/bin/env python

import argparse

from dash import fb

def main():
    parser = argparse.ArgumentParser(description='Scrape Facebook for daily stats.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    fb.snapshot_facebook( verbose=arg.verbose )

if __name__=='__main__':
    main()
