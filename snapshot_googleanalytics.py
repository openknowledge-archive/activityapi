#!/usr/bin/env python

import argparse
import os
from lib.backend import Session
from lib.backend.model import SnapshotOfAnalytics
from apiclient.errors import HttpError
from apiclient.discovery import build
from oauth2client.client import AccessTokenRefreshError
import httplib2
from oauth2client.file import Credentials
from pprint import pprint
from datetime import datetime,timedelta

def snapshot_googleanalytics(verbose=False):
    googleanalytics_auth_json=os.environ.get('GOOGLEANALYTICS_AUTH')
    # Authenticate and construct service.
    service = initialize_service(googleanalytics_auth_json)
    date_string = (datetime.now()-timedelta(days=4)).date().isoformat()
    if verbose:
        print 'Snapshotting for '+date_string
    for x in iterate_profiles(service):
        try:
            profile_id = x['id']
            # How long since we scraped this account?
            latest = Session.query(SnapshotOfAnalytics)\
                    .filter(SnapshotOfAnalytics.website==x['name'])\
                    .order_by(SnapshotOfAnalytics.timestamp.desc())\
                    .first()
            day = (datetime.now()-timedelta(days=1)).date()
            if latest and latest.timestamp>=day:
                if verbose: print ' -> most recent snapshot for %s has already been processed.' % x['name']
                continue
            hits = get_hits(service, profile_id, day.isoformat())
            sn = SnapshotOfAnalytics(timestamp=day,website=x['name'],hits=hits)
            Session.add(sn)
            if verbose:
                print '%s: %d' % (x['name'], hits)
        except Exception, e:
            print e
    Session.commit()

def initialize_service(googleanalytics_auth_json):
  # Create an httplib2.Http object to handle our HTTP requests.
  http = httplib2.Http()
  # Prepare credentials, and authorize HTTP object with them.
  assert googleanalytics_auth_json,'No GOOGLEANALYTICS_AUTH set in environment. This should be the sample.dat file created by authenticating a sample app with Google Analytics.\n\n  Read: https://developers.google.com/analytics/solutions/articles/hello-analytics-api'
  credentials = Credentials.new_from_json(googleanalytics_auth_json)
  if credentials is None or credentials.invalid:
    credentials = run(FLOW, storage)
  http = credentials.authorize(http)
  # Retrieve service.
  return build('analytics', 'v3', http=http)

def iterate_profiles(service):
  accounts = service.management().accounts().list().execute()
  if accounts.get('items'):
    firstAccountId = accounts.get('items')[0].get('id')
    webproperties = service.management().webproperties().list(
        accountId=firstAccountId).execute()
    for webproperty in webproperties.get('items',[]):
        property_id = webproperty.get('id')
        profiles = service.management().profiles().list(
            accountId=firstAccountId,
            webPropertyId=property_id).execute()
        for profile in profiles.get('items',[]):
            yield profile

def get_hits(service, profile_id, date_string):
    result= service.data().ga().get(
            ids='ga:' + profile_id,
            start_date=date_string,
            end_date=date_string,
            metrics='ga:visits').execute()
    return int(result.get('rows',[[u'0']])[0][0])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Snapshot the OKFN\' Google Analytics account for the day.')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='Verbose output')
    arg = parser.parse_args()
    snapshot_googleanalytics(verbose=arg.verbose)
