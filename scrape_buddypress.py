#!/usr/bin/env python

from dash import buddypress
import argparse
import os
import random

def main():
    parser = argparse.ArgumentParser(description='Scrape the buddypress user DB into our activity DB')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('-e', default='http://staging.okfn.org/api/okfn/get_users', dest='endpoint', help='Endpoint to connect to')
    arg = parser.parse_args()

    auth_hash = os.environ.get('BUDDYPRESS_AUTH_HASH')
    assert auth_hash, 'Error: No BUDDYPRESS_AUTH_HASH variable is set.\n  This is the pw hash of the user "zcron" in Buddypress.\n  Get it from the MySQL server, or from the live Heroku environment.'

    payload = {'auth':auth_hash,'dont_cache':random.random()} # This needs to come from environment

    usermap = buddypress.scrape_users(arg.endpoint,payload,arg.verbose)
    assert len(usermap)>100, 'Expected a lot more users than that (got %d). Something is wrong.' % len(usermap)

    buddypress.save_users(usermap,arg.verbose)


if __name__=='__main__':
    main()
