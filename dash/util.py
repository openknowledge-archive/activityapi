import csv
import re
import string

def clean_user(user):
    """Remove NULL strings and tidy user parameters"""
    for (k,v) in user.items():
        if v=='NULL':
            user[k]=None
    user['_twitter'] = user['twitter']
    user['twitter'] = clean_twitter(user['twitter'])

def clean_twitter(t):
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

