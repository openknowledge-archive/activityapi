import dash.util
from dash.backend import Session, model
from time import gmtime, strftime
import requests
import json

def _json(url,payload=None,verbose=True):
    r = requests.get( url, params=payload )
    if verbose:
        print r.url
    assert r.status_code==200
    return json.load( r.raw )

def scrape_timestamp():
    timestring = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    t = model.Timestamp(timestring)
    Session.add(t)
    Session.commit()


def scrape_members( url ):
    obj = _json(url)
    print 'Received %d rows from database.' % len(obj)
    map(dash.util.clean_user, obj)

    twitters = filter(bool, [ user['twitter'] for user in obj ])
    #print 'Got %d valid Twitter handles: %s...' % (len(twitters), ', '.join(twitters[:8]))
    print map(str,twitters)


