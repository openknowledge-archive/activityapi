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
    day = timedelta(days=1)
    today = datetime.now().date()
    until = today - day
    latest = Session.query(model.SnapshotOfFacebook)\
            .order_by(model.SnapshotOfFacebook.timestamp.desc())\
            .first()
    # By default, gather 30 days of snapshots
    since = until - timedelta(days=30)
    if latest:
        if latest.timestamp>=until:
            if verbose: print ' -> most recent snapshots have already been processed.'
            return
        since = latest.timestamp + day
    timestamp = since
    while timestamp <= until:
        data = {}
        data['likes'] = likes
        data['timestamp'] = timestamp
        snapshot = model.SnapshotOfFacebook(**data)
        if verbose: print '  -> ',snapshot.toJson()
        Session.add(snapshot)
        timestamp += timedelta(days=1)
    Session.commit()
