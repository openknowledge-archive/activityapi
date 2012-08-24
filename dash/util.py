import csv
import re
import string
import json
import requests

def download_json(url,payload=None):
    r = requests.get( url, params=payload )
    assert r.status_code==200
    return json.loads( r.text )

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
        f = {x:y for (x,y) in freq_table.items() if len(x) > min_word_length }
    tuples = filter( lambda x:x[1]>min_matches, f.items() )
    tuples = sorted( tuples, key=lambda x:x[1], reverse=True)[:results]
    return tuples

