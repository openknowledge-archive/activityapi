import feedparser
from time import mktime
from datetime import datetime

def _dictize(entry):
    try:
        author = entry.author_detail.name
    except AttributeError:
        try:
            author = entry.author
        except AttributeError:
            author = ''
    try:
        description = entry.summary
    except AttributeError: 
        try:
            description = entry.content[0].value
        except AttributeError:
            description = ''
    date = datetime.fromtimestamp(mktime(entry.updated_parsed))
    return {
        'author': author,
        'title': entry.title,
        'source_url': entry.link,
        'description': description
    }

def gather(url):
    feed = feedparser.parse(url)
    return [ _dictize(x) for x in feed.entries ]

