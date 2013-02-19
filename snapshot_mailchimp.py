#!/usr/bin/env python

import argparse
import os
from postmonkey import PostMonkey
from pprint import pprint
from datetime import datetime,timedelta
from lib.backend import Session, model

def snapshot_mailchimp(verbose=False):
    api_key = os.environ.get('MAILCHIMP_API_KEY')
    assert api_key, 'No MAILCHIMP_API_KEY defined in environment.'
    pm = PostMonkey(api_key, timeout=10)
    ping_string = pm.ping()
    expected = u'Everything\'s Chimpy!'
    assert ping_string==expected, 'Bad handshake, got "%s", expected "%s"' % (ping_string,expected)
    if verbose:
        print 'handshake ok'
    lists = pm.lists()
    if not 'data' in lists:
        print 'Got bad lists object from server.'
        pprint(lists)
        raise ValueError('Bad lists object from server')
    # Snapshot creation code...
    today = datetime.now().date()
    for l in lists['data']:
        try:
            if verbose: print 'Scraping %s...' % l['name']
            latest = Session.query(model.SnapshotOfMailchimp)\
                    .filter(model.SnapshotOfMailchimp.name==l['name'])\
                    .order_by(model.SnapshotOfMailchimp.timestamp.desc())\
                    .first()
            if latest and latest.timestamp>=today:
                if verbose: print ' -> most recent snapshots have already been processed.'
                continue
            snapshot = model.SnapshotOfMailchimp(\
                    name = l['name'],\
                    members = l['stats']['member_count'],
                    timestamp = today)
            if verbose: print '  -> ',snapshot.toJson()
            Session.add(snapshot)
            Session.commit()
        except Exception, e:
            pprint({'list':l,'exception':str(e)})

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape Mailchimp for daily stats.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_mailchimp( verbose=arg.verbose )
