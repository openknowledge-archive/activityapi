#!/usr/bin/env python

import dash.buddypress
import argparse
import os
import random


if __name__=='__main__':
    auth_hash = os.environ.get('BUDDYPRESS_AUTH_HASH')
    parser = argparse.ArgumentParser(description='Scrape the buddypress user DB into our activity DB')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()

    if not auth_hash:
        raise ValueError('Error: No BUDDYPRESS_AUTH_HASH variable is set.\n  This is the pw hash of the user "zcron" in Buddypress.\n  Get it from the MySQL server, or from the live Heroku environment.')
    endpoint = 'http://staging.okfn.org/api/okfn/get_users'
    payload = {'auth':auth_hash,'dont_cache':random.random()} # This needs to come from environment

    usermap = dash.buddypress.scrape_remote(endpoint,payload,arg.verbose)
    if len(usermap)<100:
        raise ValueError('Expected a lot more users than that (got %d). Something is wrong.' % len(usermap))
    dash.buddypress.update_local(usermap,arg.verbose)

