
def list_mailman_lists(verbose=False):
    """Scrape the server for a catalogue of all mailman lists."""
    r = requests.get('http://lists.okfn.org')
    if verbose: print 'Fetching %s' % r.url
    tree = html.fromstring( r.text )
    out = []
    for row in tree.cssselect('tr'):
        links = row.cssselect('a')
        cells = row.cssselect('td')
        if len(links)==1 and len(cells)==2:
            name = links[0].text_content()
            link = links[0].attrib['href']
            description = cells[1].text_content()
            if 'listinfo' in link:
                out.append({'name':name,'link':link})
    if verbose: print 'Got %d mailman lists' % len(out)
    return out

