import os
from postmonkey import PostMonkey
from pprint import pprint
from datetime import datetime,timedelta
from dash.backend import Session, model

###  Snapshot mailchimp 

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
    day = timedelta(days=1)
    today = datetime.now().date()
    until = today - day
    latest = Session.query(model.SnapshotOfMailchimp)\
            .order_by(model.SnapshotOfMailchimp.timestamp.desc())\
            .first()
    # By default, gather 30 days of snapshots
    since = until - timedelta(days=30)
    if latest:
        if latest.timestamp>=until:
            if verbose: print ' -> most recent snapshots have already been processed.'
            return
        since = latest.timestamp + day
    lists_raw = pm.lists()
    for l in lists_raw['data']:
        timestamp = since
        while timestamp <= until:
            data = {}
            data['name'] = l['name']
            data['members'] = l['stats']['member_count']
            data['timestamp'] = timestamp
            snapshot = model.SnapshotOfMailchimp(**data)
            if verbose: print '  -> ',snapshot.toJson()
            Session.add(snapshot)
            timestamp += timedelta(days=1)
        Session.commit()
