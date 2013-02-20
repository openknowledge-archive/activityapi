#!/usr/bin/env python

import argparse
from lxml import html
import requests
from lib import util
from lib.backend import Session
from lib.backend.model import ActivityInMailman
from datetime import datetime

def get_activity(verbose=False):
    lists = util.list_mailman_lists(verbose)
    for l in lists:
        if verbose: print 'Processing activity for %s...' % l['name']
        latest = Session.query(ActivityInMailman)\
                .filter(ActivityInMailman.list_name==l['name'])\
                .order_by(ActivityInMailman.message_id.desc())\
                .first()
        # Walk through message history from the web front-end
        archive_url = l['link'].replace('mailman/listinfo','pipermail')
        limit = 1000
        latest_id = latest.message_id if latest else -1
        for msg in _yield_messages(archive_url,latest_id, verbose=verbose):
            if verbose: print '  -> got msg #%d (%s: "%s")' % (msg['id'],msg['email'],msg['subject'])
            Session.add( ActivityInMailman(
                list_name  = l['name'],
                message_id = msg['id'], 
                subject = msg['subject'],
                author = msg['author'],
                email = msg['email'],
                link = msg['link'],
                timestamp = msg['date'] ) )
            limit -= 1
            #if limit==0: 
            #if verbose: print '  -> Reached activity limit (100)'
            #break;
        Session.commit()

def _yield_messages(url, latest_id, verbose=False):
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

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Scrape Mailman for list data and recent activity.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    get_activity( verbose=arg.verbose )
