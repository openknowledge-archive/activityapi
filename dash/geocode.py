#!/usr/bin/env python

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
