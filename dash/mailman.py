from lxml import html
import requests
import os
from dash.backend import Session
from dash.backend.model import Mailman, SnapshotOfMailman, ActivityInMailman
from datetime import datetime,timedelta
from StringIO import StringIO
from gzip import GzipFile
from tempfile import mkstemp
from mailbox import mbox
import re


###  Maintain a database of mailman lists

def scrape_mailman(verbose=False):
    """Scrape the server for a catalogue of all mailman lists."""
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
    if verbose: print 'Got %d mailman lists' % len(out)
    return out

def save_mailman( mailman, verbose=False ):
    # Add and update
    for k,v in mailman.items():
        l = Session.query(Mailman).filter(Mailman.name==k).first()
        if l:
            l.update(k,v['link'],v['description'])
        else:         
            if verbose: print 'Adding new list %s' % k
            l = Mailman(k,v['link'],v['description'])
            Session.add( l )
    # Delete
    for ml in Session.query(Mailman):
        if not ml.name in mailman:
            if verbose: print 'Deleting old list %s' % ml.name
            Session.delete(ml)
    Session.commit()


###  Get mailman activity

def scrape_activity(verbose=False):
    for l in Session.query(Mailman):
        if verbose: print 'Processing activity for %s...' % l.name
        latest = Session.query(ActivityInMailman)\
                .filter(ActivityInMailman.mailman_id==l.id)\
                .order_by(ActivityInMailman.message_id.desc())\
                .first()

        # Walk through message history from the web front-end
        archive_url = l.link.replace('mailman/listinfo','pipermail')
        limit = 100
        latest_id = latest.message_id if latest else -1
        for msg in _iterate_messages(archive_url,latest_id, verbose=verbose):
            if verbose: print '  -> got msg #%d (%s: "%s")' % (msg['id'],msg['email'],msg['subject'])

            Session.add( ActivityInMailman(
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

def _iterate_messages(url, latest_id, verbose=False):
    if verbose: print 'Fetching list index %s...' % url
    r = requests.get(url)
    tree = html.fromstring(r.text)
    links = tree.cssselect('a:nth-child(4)')
    unique_ids = set()
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
            if out['id'] in unique_ids:
                if verbose: print '  -> BROKEN LIST violates unique ID constraint (id=%d)' % out['id']
                continue
            unique_ids.add(out['id'])
            if latest_id>=0 and out['id']<=latest_id:
                if verbose: print '  -> No further messages'
                return
            # Download further message details (date & author) from the message's page
            r = requests.get(out['link'])
            msg_tree = html.fromstring(r.text)
            tmp_date = msg_tree.cssselect('i')[0].text_content()
            # Note: Platform-specific implementations can't all handle BST/GMT strings
            tmp_date = tmp_date.replace('GMT ','').replace('BST ','')
            try:
                out['date'] = datetime.strptime(tmp_date,'%a %b %d %H:%M:%S %Y')
            except ValueError as e:
                if verbose: print 'Couldnt handle date "%s"' % tmp_date
                return
            out['email'] = msg_tree.cssselect('a')[0].text_content().strip().replace(' at ','@')
            yield out


###  Snapshot all mailman lists ( # subscribers, # posts per day )

def snapshot_mailman(verbose=False):
    day = timedelta(days=1)
    today = datetime.now().date()
    until = today - day
    for l in Session.query(Mailman):
        if verbose: print 'Processing snapshots for %s...' % l.name
        latest = Session.query(SnapshotOfMailman)\
                .filter(SnapshotOfMailman.mailman_id==l.id)\
                .order_by(SnapshotOfMailman.timestamp.desc())\
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
        # Create a snapshot of each day
        for date in _daterange(since,until):
            posts_today = Session.query(ActivityInMailman)\
                            .filter(ActivityInMailman.mailman_id==l.id)\
                            .filter(ActivityInMailman.timestamp.between(date,date+day))\
                            .count()
            o = SnapshotOfMailman( date, l.id, num_subscribers, posts_today )
            Session.add(o)
            if verbose: print '  -> ',o.toJson()
        # Walk through message history, counting messages per day
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
    
