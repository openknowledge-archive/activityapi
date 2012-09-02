# Twitter

#### Methods for deailing with lists via tweepy

    def _list_name(username):
        """Look up which partitioned list is used to monitor this user"""
        l = username[0] 
        if l<'0': raise ValueError(l)
        if l<='_': return LISTS[0]
        if l<='d': return LISTS[1]
        if l<='j': return LISTS[2]
        if l<='r': return LISTS[3]
        if l<='z': return LISTS[4]
        raise ValueError(l)

    def add_all(names,lists):
        for x in names:
            try:
                lists[_list_name(x)].add_member(x)
                print 'done:',x
            except tweepy.error.TweepError:
                print 'failed to add',x

    def all_members(api,lst):
        """Which users are in this list?"""
        c = tweepy.Cursor(api.list_members,lst.user.screen_name,lst.slug)
        return [x for x in c.items()]



# Mailman

#### Methods for processing GZIPped mailman archives
#### (eg. data mining distant history)
#### Updated daily; not suitable for realtime activity tracking.

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


# Geocoding

#### Methods to geocode location strings into useful lat/long coordinates.
#### Uses the geonames.org api.

    import csv
    import time
    import json
    import urllib
    from collections import defaultdict
    import hashlib
    import math

    import common

    MEMBERS_GEO = 'cache/members.geo.json'
    MEMBERS_GEOJSON = 'cache/members.geojson.json'

    def geocode_data():
        '''Geocode the string locations using geonames.'''
        report_file = MEMBERS_GEO + '.report.json'
        report = []
        data = json.load(open(MEMBERS_RAW))
        geocode_username = common.config.get('geocode', 'username')
        baseurl = 'http://api.geonames.org/searchJSON?maxRows=1&username=%s&q=' % geocode_username
        for value in data:
            if 'location' in value:
                loc = value['location']
                loc = loc.encode('utf8', 'ignore')
                # loc = loc.replace
                _url = baseurl + urllib.quote(loc)
                fo = urllib.urlopen(_url)
                res = fo.read()
                res = json.loads(res)
                if res['geonames']:
                    value['spatial'] = res['geonames'][0]
                    msg = 'Matched ok: %s to %s' % (loc,
                            res['geonames'][0]['name'].encode('utf8', 'ignore'))
                    status = 'ok'
                else:
                    status = 'error'
                    msg = 'Failed to match: %s' % loc
                report.append([value['id'], status, msg])
                print msg
                time.sleep(0.5) 
        fileobj = open(MEMBERS_GEO, 'w')
        json.dump(data, fileobj, indent=2, sort_keys=True)
        json.dump(report, open(report_file), indent=2, sort_keys=True)

    def geojson():
        '''Convert geonames style data to geojson.'''
        data = json.load(open(MEMBERS_GEO))
        for value in data:
            if 'spatial' in value:
                cur = value['spatial']
                # add some jitter
                username = value['id']
                jitter = float(int(hashlib.md5(username).hexdigest(), 16)) % (2*math.pi)
                radius = 0.05
                lng = cur['lng'] + math.cos(jitter)*radius
                lat = cur['lat'] + math.sin(jitter)*radius
                out = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [ lng, lat ]
                    },
                    'properties': {
                        'country': cur['countryName'],
                        'country_code': cur.get('countryCode', None),
                        'name': value['location']
                    }
                }
                value['spatial'] = out
        fileobj = open(MEMBERS_GEOJSON, 'w')
        json.dump(data, fileobj, indent=2, sort_keys=True)


# RSS feed parsing

#### Methods to pull data from an RSS feed
#### (Currently we don't inspect RSS activity...)

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

