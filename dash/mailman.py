from lxml import html
import requests
import os
from dash.backend import Session
from dash.backend.model import MailingList, SnapshotOfMailingList
from datetime import datetime
from StringIO import StringIO
from gzip import GzipFile
from tempfile import mkstemp
from mailbox import mbox

def scrape_mailinglists(verbose=False):
    """Scrape the server for a catalogue of all mailing lists."""
    r = requests.get('http://lists.okfn.org')
    if verbose: print 'Fetching %s' % r.url
    tree = html.fromstring( r.text )
    out = {}
    for row in tree.cssselect('tr'):
        links = row.cssselect('a')
        cells = row.cssselect('td')
        if len(links)==1 and len(cells)==2:
            name = links[0].text_content()
            link = links[0].attrib['href']
            description = cells[1].text_content()
            if 'listinfo' in link:
                out[name] = { 'link':link, 'description':description }
    if verbose: print 'Got %d mailinglists' % len(out)
    return out

def save_mailinglists( mailinglists, verbose=False ):
    # Add and update
    for k,v in mailinglists.items():
        v['list'] = Session.query(MailingList).filter(MailingList.name==k).first()
        if v['list']: 
            v['list'].update(k,v['link'],v['description'])
        else:         
            if verbose: print 'Adding new list %s' % k
            v['list'] = MailingList(k,v['link'],v['description'])
            Session.add( v['list'] )
    # Delete
    for ml in Session.query(MailingList):
        if not ml.name in mailinglists:
            if verbose: print 'Deleting old list %s' % ml.name
            Session.delete(ml)
    # Commit now to ensure list.id is auto-assigned
    Session.commit()
    # Snapshot
    now = datetime.now()
    for k,v in mailinglists.items():
        if verbose: print 'Processing snapshot for %s...' % k
        mailinglist_id = v['list'].id
        subscribers = len(scrape_subscribers(k, mailinglists))
        posts_today = 0
        if verbose: print '  posts=%d subscribers=%d' % (posts_today,subscribers)
        snapshot = SnapshotOfMailingList( now, mailinglist_id, subscribers, posts_today )
        Session.add(snapshot)
    Session.commit()

def scrape_subscribers(list_name, all_lists, verbose=False):
    """Access the list's roster and generate 
       a text->href list of members of this list."""
    url = all_lists[list_name]['link'].replace('listinfo','roster')
    # admin@okfn.org can access list rosters
    payload={'roster-email':'admin@okfn.org', 'roster-pw':os.environ.get('MAILMAN_ADMIN_PW')}
    if verbose: print 'Scraping subscriber list for %s...' % list_name
    r = requests.post(url, data=payload)
    # Did we get in?
    if 'roster authentication failed' in r.text:
        raise ValueError('Roster authentication failed. Bad password.')
    # Scrape all the links to email--at--domain.com
    tree = html.fromstring( r.text )
    _links = tree.cssselect('a')
    links = filter( lambda x: '--at--' in x.attrib['href'], _links )
    return { x.text_content : x.attrib['href'] for x in links }
    
def iterate_messages(url, verbose=False, since_date=None, max_months=0):
    if verbose: print 'Fetching list index %s...' % url
    r = requests.get(url)
    tree = html.fromstring(r.text)
    _date_links = tree.cssselect('a')
    date_links = [ url+x.attrib['href'] for x in _date_links if x.attrib['href'].endswith('.gz') ]
    count=0
    for url in date_links:
        if max_months and count==max_months:
            if verbose: print '  -> Returned max (%d) months' % max_months
            return
        if verbose: print '  -> %s' % url
        source_url = url.replace('.txt.gz','/')
        mailbox = _url_to_mailbox(url)
        for message in mailbox:
            if since_date and message['date']<=since_date:
                if verbose: print '  -> Reached since_date.' 
                return
            message['source_url'] = source_url
            yield message
        count += 1

def _url_to_mailbox(url):
    r = requests.get(url)
    buf = StringIO(r.content)
    content = GzipFile(fileobj=buf, mode='rb').read()
    # mbox requires we dump this to a temp file
    tmp = mkstemp()[1]
    f = open(tmp,'w')
    f.write(content)
    f.close()
    out = [ _dictize_message(x) for x in mbox(tmp) ]
    # Descending chronological order
    return sorted(out, key=lambda x:x['date'], reverse=True)

def _dictize_message(message):
    subjects = message.get_all('Subject')
    subject = subjects[-1] if subjects else '(No Subject)'
    
    dates = message.get_all('Date')
    date = dates[-1] if dates else '(No date)'
    date = date.rsplit(' +', 1)[0].rsplit(' -', 1)[0].strip()
    date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S')
    return {
        'author': message.get_from().split('  ')[0],
        'title': subject,
        'date' : date,
        }


