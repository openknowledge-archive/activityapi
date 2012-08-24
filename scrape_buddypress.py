#!/usr/bin/env python

import dash.buddypress
import argparse
import os
import random

def main():
    auth_hash = os.environ.get('BUDDYPRESS_AUTH_HASH')
    parser = argparse.ArgumentParser(description='Scrape the buddypress user DB into our activity DB')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('-e', default='http://staging.okfn.org/api/okfn/get_users', dest='endpoint', help='Endpoint to connect to')
    arg = parser.parse_args()

    if not auth_hash:
        raise ValueError('Error: No BUDDYPRESS_AUTH_HASH variable is set.\n  This is the pw hash of the user "zcron" in Buddypress.\n  Get it from the MySQL server, or from the live Heroku environment.')
    payload = {'auth':auth_hash,'dont_cache':random.random()} # This needs to come from environment

    usermap = dash.buddypress.scrape_remote(arg.endpoint,payload,arg.verbose)
    if len(usermap)<100:
        raise ValueError('Expected a lot more users than that (got %d). Something is wrong.' % len(usermap))
    dash.buddypress.update_local(usermap,arg.verbose)


if __name__=='__main__':
    main()
