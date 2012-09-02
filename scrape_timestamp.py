#!/usr/bin/env python

import argparse
from dash.backend import Session
from dash.backend.model import Timestamp
from time import gmtime, strftime

def main():
    parser = argparse.ArgumentParser(description='Insert the current timestamp into the database. Used to track uptime, debugging etc.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    timestring = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    if arg.verbose: print 'Adding timestamp %s...' % timestring
    t = Timestamp(timestring)
    Session.add(t)
    Session.commit()

if __name__=='__main__':
    main()
