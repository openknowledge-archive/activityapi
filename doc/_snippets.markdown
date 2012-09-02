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

