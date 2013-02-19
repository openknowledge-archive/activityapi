# OKFN Activity API

http://activityapi.herokuapp.com

## Local installation

#### Prerequisites:
 
    # Create a Postgres database and configure an environment variable:
    export DATABASE_URL=postgresql://user:pass@localhost/mydatabase 

#### Run the front-end

    # Install the dashboard requirements
    virtualenv env.dashboard
    . env.dashboard/bin/activate
    pip install -r requirements.txt
    # Start the server
    ./frontend.py

#### Run the Timestamp scraper (debug)

    # This simple scraper will populate the database 
    # with an extra row each time it is run:
    ./scrape_timestamp.py

#### Run the Twitter scraper

    # Grab a daily snapshot of twitter statistics for our accounts.
    # The account list is coded into the script.
    ./scrape_twitter.py --verbose

#### Run the Buddypress scraper

    # The scraper connects to a Wordpress plugin running on our Wordpress/Buddypress/MySQL servers.
    # You'll need to get the auth key and store it in an environment variable.
    export BUDDYPRESS_AUTH_HASH='$P$B8Bqng....

    # You can then run the scraper
    ./scrape_buddypress.py --verbose

#### Run the Github scraper

    # The scraper connects to the public Github API to download user activity.
    ./scrape_github.py activity --verbose

    # It also runs a daily job to snapshot the watchers, forks and other statistics of our repositories.
    ./scrape_github.py daily --verbose

#### Run the Mailman scraper
    
    # The scraper connects to the public Mailman archives to download user activity.
    ./scrape_mailman.py activity --verbose

    # It also runs a daily job to snapshot the number of subscribers and daily posts to each mailing list.
    # This accesses the subscriber roster, which requires a password set in an environment variable.
    # NOTE: This will record 0 posts-per-day unless the activity scraper has been run first!
    export MAILMAN_ADMIN=password1234...
    ./scrape_mailman.py daily --verbose


## In Production
The system is deployed on Heroku. `Procfile` declares the web frontend to be run. The Scheduler add-on runs each of the `scrape_*.py` scripts at regular intervals to keep the database up-to-date.

## Interactive Mode

You can interact with the database and scrapers via Python's interactive terminal. For example:

    (%activityapi)$ DATABASE_URL=postgresql://localhost/zephod python
    Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05) 
    [GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2335.15.00)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from dash.backend import model,Session

Pull tweets from the database:

    >>> query = Session.query(model.Tweet).order_by(model.Tweet.timestamp.desc()).limit(5)
    >>> query[0].json()
    {'screen_name': u'rabble', 'text': u"I've watched it streamed, but this year i plan on attending the rebranded Lean Startup Conference. http://t.co/YanScM8E Dec 3-4", 'tweet_id': 230419555657338880L, 'timestamp': '2012-07-31T21:47:57', 'geo': None, 'id': 6}
    >>> 
    >>> from pprint import pprint
    >>> pprint( [ x.json() for x in query ] )
    [{'geo': None,
      'id': 4170,
      'screen_name': u'jburnmurdoch',
      'text': u"Excellent tournament for Laura Robson, first time she's comprehensively outshone Watson at a senior slam. Bright futures for both.",
      'timestamp': '2012-09-02T22:44:12',
      'tweet_id': 242392508435427328L},
     {'geo': None,
      'id': 3018,
    ...

How many twitter API hits remain?

    >>> import json
    >>> json.dumps( twitter.get_api().rate_limit_status() )
    '{"reset_time": "Tue Aug 21 15:29:48 +0000 2012", "remaining_hits": 215, "reset_time_in_seconds": 1345562988, "hourly_limit": 350, "photos": {"daily_limit": 30, "reset_time": "Wed Aug 22 14:45:01 +0000 2012", "remaining_hits": 30, "reset_time_in_seconds": 1345646701}}'
