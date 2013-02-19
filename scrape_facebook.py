#!/usr/bin/env python

import argparse
import os
import facebook
from pprint import pprint
from datetime import datetime,timedelta
from dash.backend import Session, model

def snapshot_facebook(verbose=False):
    api = facebook.GraphAPI()
    obj = api.get_object('/OKFNetwork')
    if not 'likes' in obj:
        print 'Got bad object from server.'
        pprint(obj)
        raise ValueError('Bad object from server')
    likes = obj['likes']
    if verbose:
        print 'Likes today: %d' % likes
    # Snapshot creation code...
    today = datetime.now().date()
    latest = Session.query(model.SnapshotOfFacebook)\
            .order_by(model.SnapshotOfFacebook.timestamp.desc())\
            .first()
    if latest and latest.timestamp>=today:
        if verbose: print ' -> most recent snapshots have already been processed.'
        return
    snapshot = model.SnapshotOfFacebook(likes=likes, timestamp=today)
    if verbose: print '  -> ',snapshot.toJson()
    Session.add(snapshot)
    Session.commit()

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape Facebook for daily stats.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_facebook( verbose=arg.verbose )
