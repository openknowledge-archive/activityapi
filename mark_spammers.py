#!/usr/bin/env python

from dash.backend import Session
from dash.backend.model import Person
import requests
import argparse
import os
import json
import random

def main():
    auth_hash = os.environ.get('BUDDYPRESS_AUTH_HASH')
    parser = argparse.ArgumentParser(description='Mark Buddypress users as spammers where they have been flagged in our DB')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    parser.add_argument('-e', default='http://staging.okfn.org/api/okfn/mark_spammer', dest='endpoint', help='Endpoint to connect to')
    arg = parser.parse_args()

    if not auth_hash:
        raise ValueError('Error: No BUDDYPRESS_AUTH_HASH variable is set.\n  This is the pw hash of the user "zcron" in Buddypress.\n  Get it from the MySQL server, or from the live Heroku environment.')

    # List spammers from the database
    q = Session.query(Person).filter(Person._opinion=='spam')
    spammers = { x.user_id:x.login for x in q }
    print 'Got %d spammers...' % len(spammers)
    print json.dumps(spammers)

    for user_id,login in spammers.iteritems():
        print 'Marking %s...' % login
        payload = {
                'auth':auth_hash,
                'dont_cache':random.random(),
                'id':user_id,
                'is_spammer':True
                } # This needs to come from environment
        r = requests.get(arg.endpoint, params=payload)
        if not r.status_code==200:
            print r.status_code, payload, r, r.text
        else:
            response = json.loads(r.text)
            if not response['status']=='ok':
                print response['status'], payload, response

if __name__=='__main__':
    main()
