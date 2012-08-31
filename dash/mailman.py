from lxml import html
import requests
import os
from dash.backend import Session
from dash.backend.model import MailingList, SnapshotOfMailingList, ActivityInMailingList
from datetime import datetime,timedelta
from StringIO import StringIO
from gzip import GzipFile
from tempfile import mkstemp
from mailbox import mbox
import re


###  Maintain a database of mailing lists

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
        l = Session.query(MailingList).filter(MailingList.name==k).first()
        if l:
            l.update(k,v['link'],v['description'])
        else:         
            if verbose: print 'Adding new list %s' % k
            l = MailingList(k,v['link'],v['description'])
            Session.add( l )
    # Delete
    for ml in Session.query(MailingList):
        if not ml.name in mailinglists:
            if verbose: print 'Deleting old list %s' % ml.name
            Session.delete(ml)
    Session.commit()


###  Get mailinglist activity

def scrape_activity(verbose=False):
    for l in Session.query(MailingList):
        if verbose: print 'Processing activity for %s...' % l.name
        latest = Session.query(ActivityInMailingList)\
                .filter(ActivityInMailingList.mailinglist_id==l.id)\
                .order_by(ActivityInMailingList.message_id.desc())\
                .first()

        # Walk through message history from the web front-end
        archive_url = l.link.replace('mailman/listinfo','pipermail')
        limit = 100
        latest_id = latest.message_id if latest else 0
        for msg in _iterate_messages_individual(archive_url,latest_id, verbose=verbose):
            if verbose: print '  -> got msg #%d (%s: "%s")' % (msg['id'],msg['email'],msg['subject'])

            Session.add( ActivityInMailingList(
                l.id, 
                msg['id'], 
                msg['subject'],
                msg['author'],
                msg['email'],
                msg['link'],
                msg['date'],
                    ) )
            limit -= 1
            if limit==0: 
                if verbose: print '  -> Reached activity limit (100)'
                break;
        Session.commit()

def _iterate_messages_individual(url, latest_id, verbose=False):
    if verbose: print 'Fetching list index %s...' % url
    r = requests.get(url)
    tree = html.fromstring(r.text)
    links = tree.cssselect('a:nth-child(4)')
    for link in links:
        month_url = url+'/'+link.attrib['href']
        base_url = month_url.replace('date.html','')
        r = requests.get(month_url)
        tree = html.fromstring(r.text)
        ul = tree.cssselect('ul')[1]
        lis = ul.cssselect('li') 
        # Why does mailman serve me ascending chronological order?
        lis.reverse()
        for li in lis:
            a = li.cssselect('a')
            out = {
                'author' : li.cssselect('i')[0].text_content().strip(),
                'link' : base_url + a[0].attrib['href'],
                'subject' : a[0].text_content().strip(),
                'id' : int( a[1].attrib['name'] )
            }
            if latest_id and out['id']==latest_id:
                if verbose: print '  -> No further messages'
                return
            # Download further message details (date & author) from the message's page
            r = requests.get(out['link'])
            msg_tree = html.fromstring(r.text)
            tmp_date = msg_tree.cssselect('i')[0].text_content() 
            out['date'] = datetime.strptime(tmp_date,'%a %b %d %H:%M:%S %Z %Y')
            out['email'] = msg_tree.cssselect('a')[0].text_content().strip().replace(' at ','@')
            yield out


###  Snapshot all mailinglists ( # subscribers, # posts per day )

def snapshot_mailinglists(verbose=False):
    day = timedelta(days=1)
    today = datetime.now().date()
    until = today - day
    for l in Session.query(MailingList):
        if verbose: print 'Processing snapshots for %s...' % l.name
        latest = Session.query(SnapshotOfMailingList)\
                .filter(SnapshotOfMailingList.mailinglist_id==l.id)\
                .order_by(SnapshotOfMailingList.timestamp.desc())\
                .first()
        # By default, gather 30 days of snapshots
        since = until - timedelta(days=30)
        if latest:
            if latest.timestamp>=until:
                if verbose: print ' -> most recent snapshots have already been processed.'
                continue
            since = latest.timestamp + day
        # Download subscriber list
        roster_url = l.link.replace('listinfo','roster')
        num_subscribers = len(_scrape_subscribers(roster_url, verbose=verbose))
        # Walk through message history, counting messages per day
        post_tally = { x:0 for x in _daterange(since,until) }
        archive_url = l.link.replace('mailman/listinfo','pipermail')
        for message in _iterate_message_archives(archive_url,verbose):
            d = message['date'].date()
            if d < since:
                break
            if d <= until:
                post_tally[ d ] += 1
        # Write snapshots to the database
        for (date,posts_today) in post_tally.items():
            o = SnapshotOfMailingList( date, l.id, num_subscribers, posts_today )
            Session.add(o)
            if verbose: print '  -> ',o.json()
        if verbose: print '  -> Done. Got %d snapshots' % len(post_tally)
        Session.commit()

def _daterange(since,until):
    out = []
    while since<=until:
        out.append(since)
        since+=timedelta(days=1)
    return out

def _scrape_subscribers(url, verbose=False):
    """Access the list's roster and generate 
       a text->href list of members of this list."""
    # admin@okfn.org can access list rosters
    payload={'roster-email':'admin@okfn.org', 'roster-pw':os.environ.get('MAILMAN_ADMIN_PW')}
    if verbose: print 'Scraping subscriber list for %s...' % url
    r = requests.post(url, data=payload)
    # Did we get in?
    if 'roster authentication failed' in r.text:
        raise ValueError('Roster authentication failed. Bad password.')
    # Scrape all the links to email--at--domain.com
    tree = html.fromstring( r.text )
    _links = tree.cssselect('a')
    links = filter( lambda x: '--at--' in x.attrib['href'], _links )
    return { x.text_content : x.attrib['href'] for x in links }
    
def _iterate_message_archives(url, verbose=False):
    if verbose: print 'Fetching list index %s...' % url
    r = requests.get(url)
    tree = html.fromstring(r.text)
    _gzip_links = tree.cssselect('a')
    gzip_links = [ url+'/'+x.attrib['href'] for x in _gzip_links if x.attrib['href'].endswith('.gz') ]
    for url in gzip_links:
        if verbose: print '  -> %s' % url
        mailbox = _scrape_gzip_archive(url)
        for message in mailbox:
            yield message

def _scrape_gzip_archive(url):
    r = requests.get(url)
    buf = StringIO(r.content)
    content = GzipFile(fileobj=buf, mode='rb').read()
    # mbox requires we dump this to a temp file
    tmp = mkstemp()[1]
    f = open(tmp,'w')
    f.write(content)
    f.close()
    # Iterate through the archive, ignoring those with no valid date attached
    out = [ _dictize_message(x) for x in mbox(tmp) if x['date'] ]
    # Descending chronological order
    return sorted(out, key=lambda x:x['date'], reverse=True)

def _dictize_message(message):
    """Utility method. Not all these fields are 
       really used, but this is how it's done."""
    subjects = message.get_all('Subject')
    subject = subjects[-1] if subjects else '(No Subject)'
    
    dates = message.get_all('Date')
    date = None
    if dates:
        tmp = dates[-1].rsplit(' +', 1)[0].rsplit(' -', 1)[0].strip()
        try:
            date = datetime.strptime(tmp, '%a, %d %b %Y %H:%M:%S')
        except ValueError:
            try:
                date = datetime.strptime(tmp, '%a, %d %b %Y %H:%M')
            except ValueError:
                pass
    # Extract an email address
    email = message.get_from().split('  ')[0]
    email = email.replace(' at ','@')
    # Extract an author name
    author = ''
    r = re.compile('\((.*)\)')
    match = r.search(message.get('from') or '')
    if match:
        author = match.group(1)
    return {
        'author': author,
        'email': email,
        'title': subject,
        'date' : date,
        }


