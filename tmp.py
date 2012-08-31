from dash.backend import Session
from dash.backend.model import SnapshotOfMailingList
from datetime import timedelta,datetime
from dash import mailman

def bucketize(num_buckets, datetimes):
    today = datetime.today().date()
    buckets = [{'day':today,'entries':[]}]
    day = timedelta(days=1)
    while num_buckets>0:
        buckets.append( { 'day': buckets[-1]['day']-day, 'entries':[] } )
        num_buckets -=1
    buckets.reverse()
    for dt in datetimes:
        for bucket in buckets:
            if dt.date()==bucket['day']:
                bucket['entries'].append(dt)
                break
        else:
            print 'datetime doesn\'t fit: ',dt
    return buckets

def createsnapshots(mailinglist):
    archive_url = mailinglist.link.replace('mailman/listinfo','pipermail')
    roster_url = mailinglist.link.replace('listinfo','roster')
    datetimes = [ x['date'] for x in mailman.iterate_messages(archive_url, verbose=True, max_months=12) ]
    buckets = bucketize(365, datetimes)
    subscribers = len(mailman.scrape_subscribers(roster_url, verbose=True))
    out = []
    for bucket in buckets:
        dt = datetime.combine( bucket['day'], datetime.min.time() )
        snapshot = SnapshotOfMailingList(dt, mailinglist.id, subscribers, len(bucket['entries']))
        Session.add(snapshot)
    Session.commit()


def imp(x):
    return SnapshotOfMailingList( datetime.fromtimestamp(x['timestamp']).date(), x['mailinglist_id'], x['subscribers'], x['posts_today'] )

def go(data):
    interval = 8
    while len(data):
        for x in data[:interval]:
            Session.add(imp(x))
        Session.commit()
        data = data[interval:]
        print len(data),'remaining'


