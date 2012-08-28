from dash.backend import Session, model
import util
import string
import re


def scrape_remote( url , payload=None, verbose=False):
    obj = util.download_json(url,payload)
    users = obj['users']
    if verbose:
        print 'Received %d rows from database.' % len(users)
    map(_clean,users)
    return { x['user_id']:x for x in users }

def update_local( usermap, verbose=False ):
    addme = set(usermap.keys())
    for existing in Session.query(model.Person):
        user_id = existing.user_id
        if user_id in usermap:
            _diff(existing, usermap[user_id], verbose)
            addme.remove( user_id )
        else:
            diff = model.PersonDiff('delete',existing)
            Session.add(diff)
            if verbose:
                print diff
            Session.delete(existing)
    for x in addme:
        user = usermap[x]
        person = model.Person.parse(user)
        Session.add(person)
        diff = model.PersonDiff('add',person)
        Session.add(diff)
        if verbose:
            print diff
    Session.commit()


## Util methods

def _clean(user):
    user['user_id'] = int(user['user_id'])
    user['_twitter'] = user['twitter']
    user['avatar'] = _clean_avatar(user['avatar'])
    user['twitter'] = _clean_twitter(user['twitter'])
    for (k,v) in user.items():
        if v==False: user[k] = None

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
        old = person.__getattribute__(k)
        if not old==v:
            # I like to track changes people make to their profiles
            diff = model.PersonDiff('update',person, {'attribute':k,'old_value':old,'new_value':v})
            if not k[0]=='_':
                # Don't store a diff if I update stupid fields like '_twitter' 
                Session.add(diff)
            if verbose:
                print diff
            changed = True
            person.__setattr__(k,v)
    if changed:
        Session.add(person)

