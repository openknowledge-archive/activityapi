from lxml import html
import requests
import os
from dash.backend import Session
from dash.backend.model import MailingList


## TODO triage
from datetime import datetime
from urllib import urlretrieve
from tempfile import mkstemp
from mailbox import mbox
import gzip


def scrape_remote():
    """Scrape the list server for a list of all mailing lists."""
    r = requests.get('http://lists.okfn.org')
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
    return out

def update_local( remote ):
    # Add and update
    for k,v in remote.items():
        obj = Session.query(MailingList).filter(MailingList.name==k).first()
        if obj:
            obj.update(k,v)
        else:
            Session.add( MailingList(k,v) )
    # Delete
    for ml in Session.query(MailingList):
        if not ml.name in remote:
            Session.delete(ml)
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
    

def _dictize(message):
    subjects = message.get_all('Subject')
    subject = subjects[-1] if subjects else '(No Subject)'
    
    dates = message.get_all('Date')
    date = dates[-1] if dates else '(No date)'
    date = date.rsplit(' +', 1)[0].rsplit(' -', 1)[0].strip()
    date = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S')
    # do not save description here as large
    # description =  message.get_payload()
    description = None
    return {
        'author': message.get_from().split('  ')[0],
        'title': subject,
        'description': description,
        'source_url': url,
        'date' : date
        }

def gather(url, how_many_months=1):
    '''Gather mailman archives info.

    :param how_many_months: how many months back to go in the archives. Set to
        <= 0 for unlimited.
    '''
    print 'gathering %s' % url
    if 'mailman/listinfo' in url:
        url = url.replace('mailman/listinfo', 'pipermail')
    return [ _dictize(message) for message in get_messages(url, how_many_months) ]

def get_messages(url, how_many_months=1):
    try:
        index = lxml.html.parse(url)
    except IOError, io:
        return []
    count = 0
    for anchor in index.findall('//a'):
        if how_many_months > 0 and count >= how_many_months:
            break
        try:
            ref = anchor.get('href')
            if ref.endswith('.gz'):
                count += 1
                log.info('Archive: %s' % ref.split('.')[0])
                ref = url + '/' + ref
                filename, headers = urlretrieve(ref)
                gzfh = gzip.open(filename, 'r')
                fh, mboxtmp = mkstemp()
                mboxfh = open(mboxtmp, 'w')
                mboxfh.write(gzfh.read())
                mboxfh.close()
                gzfh.close()
                _mbox = mbox(mboxtmp)
                return list(_mbox)
        except IOError, io:
            log.exception(io)
