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

def freq_table(tweets):
    freq = {}
    regex = re.compile(r'[\w:/#\.]+')
    for tweet in tweets:
        text = tweet.text
        for match in regex.finditer(tweet.text):
            word = match.group(0)
            freq[word] = freq.get(word,0) + 1
    return freq

def analyse(freq_table, min_word_length=7, min_matches=3, results=10, links=False, hashtags=False):
    if hashtags:
        f = {x:y for (x,y) in freq_table.items() if x[0]=='#'}
    elif links:
        f = {x:y for (x,y) in freq_table.items() if x[:5]=='http:'}
    else:
        f = {x:y for (x,y) in freq_table.items() if len(x) > min_word_length and y>min_matches}
    f = sorted( f.items(), key=lambda x:x[1], reverse=True)[:results]
    return f

