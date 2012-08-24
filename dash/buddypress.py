from dash.backend import Session, model
import util

def scrape_remote( url , payload=None, verbose=False):
    obj = util.download_json(url,payload)
    users = obj['users']
    if verbose:
        print 'Received %d rows from database.' % len(users)
    def clean(user):
        user['user_id'] = int(user['user_id'])
        for (k,v) in user.items():
            if v==False: user[k] = None
    map(clean,users)
    return { x['user_id']:x for x in users }

def _diff(person, data, verbose=False):
    changed = False
    for (k,v) in data.items():
        old = person.__getattribute__(k)
        if not old==v:
            if verbose:
                print 'Updating %s for user %s (%s)' % (k,data['login'],data['display_name'])
                print '  Old->New :: %s (%s)->%s (%s)' % (old, type(old), v, type(v))
            changed = True
            person.__setattr__(k,v)
    if changed:
        Session.add(person)

def update_local( usermap, verbose=False ):
    addme = set(usermap.keys())
    for existing in Session.query(model.Person):
        user_id = existing.user_id
        if user_id in usermap:
            _diff(existing, usermap[user_id], verbose)
            addme.remove( user_id )
        else:
            print 'deleting id=%d (login=%s, name=%s)' % (existing.user_id,existing.login,existing.display_name)
            Session.delete(existing)
    for x in addme:
        user = usermap[x]
        print 'adding id=%d (login=%s, name=%s)' % (x,user['login'],user['display_name'])
        person = model.Person.parse(user)
        Session.add(person)
    Session.commit()









