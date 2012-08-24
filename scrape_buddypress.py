#!/usr/bin/env python

import dash.buddypress
import argparse

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape the buddypress user DB into our activity DB')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')

    arg = parser.parse_args()
    endpoint = 'http://staging.okfn.org/api/okfn/get_users'
    payload = {'auth':'27b','q':'10'} # This needs to come from environment

    usermap = dash.buddypress.scrape_remote(endpoint,payload,arg.verbose)
    if len(usermap)<100:
        raise ValueError('Expected a lot more users than that (got %d). Something is wrong.' % len(usermap))
    dash.buddypress.update_local(usermap,arg.verbose)

