#!/usr/bin/env python

import dashlib
from pprint import pprint

def importcsv( filename ):
    o = dashlib.util.read_csv(filename)
    print 'Received %d rows from database.' % len(o)
    map(dashlib.util.clean_user, o)

    twitters = filter(bool, [ user['twitter'] for user in o ])
    print 'Got %d valid Twitter handles: %s...' % (len(twitters), ', '.join(twitters[:8]))
    print o[0].keys()
    return o


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Import the latest members list into the DB.')
    parser.add_argument('filename', type=str, help='CSV file to read'),
    arg = parser.parse_args()
    members = importcsv(arg.filename)

