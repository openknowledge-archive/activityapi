from dash.backend import Session, model
import dash.util
import requests
import json

def _json(url,payload=None,verbose=True):
    r = requests.get( url, params=payload )
    if verbose:
        print r.url
    assert r.status_code==200
    return json.load( r.raw )

def _clean_user(user):
    """Remove NULL strings and tidy user parameters"""
    for (k,v) in user.items():
        if v=='NULL':
            user[k]=None
    user['_twitter'] = user['twitter']
    user['twitter'] = _clean_twitter(user['twitter'])

def _clean_twitter(t):
    valid = set(string.letters + string.digits + '_')
    if t: 
        t = t.lower().strip()
        if t[0]=='@':
            t=t[1:]
        if 'twitter.com' in t:
            t = t.split('/')[-1]
        t = re.compile('[, ]').split(t)[0]
        if set(t).issubset(valid):
            return t

def scrape_members( url ):
    obj = _json(url)
    print 'Received %d rows from database.' % len(obj)
    map(_clean_user, obj)

    twitters = filter(bool, [ user['twitter'] for user in obj ])
    #print 'Got %d valid Twitter handles: %s...' % (len(twitters), ', '.join(twitters[:8]))
    print map(str,twitters)


