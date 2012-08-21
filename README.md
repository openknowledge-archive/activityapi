# OKFN Activity API

http://dash2.herokuapp.com

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

    # The scraper connects to my account(z_cron) which maintains Twitter lists of all OKFN members.
    # You'll need to get the credentials and store them in environment variables.
    export TWITTER_CONSUMER_SECRET=b1946ac9...
    export TWITTER_ACCESS_TOKEN_SECRET=591785b...
    
    # You can then run the scraper:
    ./scrape_twitter.py

## In Production
The system is deployed on Heroku. `Procfile` declares the web frontend to be run. The Scheduler add-on runs each of the `scrape_*.py` scripts at regular intervals to keep the database up-to-date.

## Interactive Mode

You can interact with the database and scrapers via Python's interactive terminal. For example:

    (%activityapi)$ DATABASE_URL=postgresql://localhost/zephod python
    Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05) 
    [GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2335.15.00)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from dash import backend

Pull tweets from the database:

    >>> query = backend.Session.query(backend.model.Tweet).limit(5)
    >>> query[0].json()
    {'screen_name': u'rabble', 'text': u"I've watched it streamed, but this year i plan on attending the rebranded Lean Startup Conference. http://t.co/YanScM8E Dec 3-4", 'tweet_id': 230419555657338880L, 'timestamp': '2012-07-31T21:47:57', 'geo': None, 'id': 6}

Scrape tweets into the database: (pass a minimum tweet\_id the first time you do this, otherwise you'll download all history)

    >>> from dash import twitter
    >>> twitter.scrape_tweets()
    Last known tweet_id: 230428104940720128
    Polling list okfn_0_9...
      -> List yielded 31 tweets
    Polling list okfn_a_d...
      -> List yielded 582 tweets
    Polling list okfn_e_j...
      -> List yielded 579 tweets
    Polling list okfn_k_r...
    Exception while polling okfn_k_r: IncompleteRead(2896 bytes read, 32001 more expected)
    Polling list okfn_s_z...
      -> List yielded 572 tweets
    => Got 1816 tweets total

How many twitter API hits remain?

    >>> import json
    >>> json.dumps( twitter.get_api().rate_limit_status() )
    '{"reset_time": "Tue Aug 21 15:29:48 +0000 2012", "remaining_hits": 215, "reset_time_in_seconds": 1345562988, "hourly_limit": 350, "photos": {"daily_limit": 30, "reset_time": "Wed Aug 22 14:45:01 +0000 2012", "remaining_hits": 30, "reset_time_in_seconds": 1345646701}}'
