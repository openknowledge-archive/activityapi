from dash.backend import Session
from dash.backend.model import Person, ActivityInBuddypress, SnapshotOfBuddypress
import string
import re
import json
import requests
from datetime import datetime,timedelta


def scrape_users( url , payload=None, verbose=False):
    obj = _scrape_endpoint(url,payload)
    users = obj['users']
    if verbose:
        print 'Received %d rows from database.' % len(users)
    map(_clean,users)
    return { x['user_id']:x for x in users }

def save_users( usermap, verbose=False ):
    addme = set(usermap.keys())
    for existing in Session.query(Person):
        user_id = existing.user_id
        if user_id in usermap:
            _diff(existing, usermap[user_id], verbose)
            addme.remove( user_id )
        else:
            diff = ActivityInBuddypress('delete',existing)
            Session.add(diff)
            if verbose:
                print diff
            Session.delete(existing)
    for x in addme:
        user = usermap[x]
        user['registered'] = _parse_date(user['registered'])
        person = Person.parse(user)
        Session.add(person)
        diff = ActivityInBuddypress('add',person)
        Session.add(diff)
        if verbose:
            print diff
    Session.commit()

## Daily stats

def snapshot_buddypress(verbose=False):
    """Create SnapshotOfBuddypress objects in the database for 
       every day since the last time this was run."""
    today = datetime.now().date()
    until = today - timedelta(days=1)
    # By default, gather 1 day of snapshots
    since = until - timedelta(days=1)
    # Move 'since' forward if snapshots exist
    latest = Session.query(SnapshotOfBuddypress)\
            .order_by(SnapshotOfBuddypress.timestamp.desc())\
            .first()
    if latest:
        if latest.timestamp>=until:
            if verbose: print ' -> most recent snapshots have already been processed.'
            return
        since = latest.timestamp + timedelta(days=1)
    num_users = Session.query(Person).count()
    while since <= until:
        snapshot = SnapshotOfBuddypress(since, num_users)
        if verbose: print '  -> ',snapshot.toJson()
        Session.add(snapshot)
        since += timedelta(days=1)
    Session.commit()


## Util methods

def _scrape_endpoint(url,payload=None):
    r = requests.get( url, params=payload )
    assert r.status_code==200
    try:
        return json.loads( r.text )
    except ValueError:
        print 'bad json:'
        print r.text
        raise ValueError('No JSON object could be decoded.')

def _clean(user):
    user['user_id'] = int(user['user_id'])
    user['_twitter'] = user['twitter']
    user['avatar'] = _clean_avatar(user['avatar'])
    user['website'] = _clean_website(user['website'])
    user['twitter'] = _clean_twitter(user['twitter'])
    for (k,v) in user.items():
        if v==False: user[k] = None

def _clean_website(website):
    """Clean up a website address from the Buddypress database"""
    if website and not website.strip()[:4].lower()=='http':
        return 'http://'+website
    return website

def _clean_avatar(avatar):
    """Clean up an avatar received from the BuddyPress database"""
    r = re.compile('<img[^>]*src="([^"]*)')
    match = r.search(avatar)
    if match:
        out = match.group(1)
        if not 'mystery-man' in out:
            return match.group(1)

def _clean_twitter(t):
    """Clean up a handle received from the BuddyPress database"""
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

def _diff(person, data, verbose=False):
    """Update the model with new key/value pairs"""
    changed = False
    for (k,v) in data.items():
        # Perhaps this should be handled elsewhere. We translate it from string to datetime.
        if k=='registered': continue
        old = person.__getattribute__(k)
        if not old==v:
            # Don't store a diff if I update stupid fields like '_twitter' 
            if not (k[0]=='_' or k=='last_active'):
                # I like to track changes people make to their profiles
                diff = ActivityInBuddypress('update',person, {'attribute':k,'old_value':str(old),'new_value':str(v)})
                Session.add(diff)
                if verbose:
                    print diff
            changed = True
            person.__setattr__(k,v)
    if changed:
        Session.add(person)

def _parse_date(date):
    parse = lambda x : datetime.strptime(x,'%Y-%m-%d %H:%M:%S')
    try:
        return parse(date)
    except Exception as e:
        from sys import stderr
        print >>stderr,'Exception processing date %s'%date, e
        return parse('2012-01-01 00:00:01')

