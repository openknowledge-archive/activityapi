# OKFN Activity API

http://activityapi.herokuapp.com

http://okfnlabs.org/dashboard

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

#### Run the Twitter scraper

    # Grab a daily snapshot of twitter statistics for our accounts.
    # The account list is coded into the script.
    ./snapshot_twitter.py --verbose

#### Run the Facebook scraper

    # Grab a daily snapshot of facebook likes statistics for our account.
    ./snapshot_facebook.py --verbose

#### Run the Google Analytics scraper

    # This runs a daily job to snapshot the web hits of all our websites.
    # You'll need to mess around with getting OAuth set up to create a sample.dat authentication file.
    # Eg. try the example scripts from: https://developers.google.com/analytics/solutions/articles/hello-analytics-api'
    # We store this file into an environment variable, GOOGLEANALYTICS_AUTH.
    # If you're hooked up to heroku, you can just steal it from there (heroku run 'echo $GOOGLEANALYTICS_AUTH')
    ./snapshot_googleanalytics.py daily --verbose

#### Run the Github scraper

    # This runs a daily job to snapshot the watchers, forks and other statistics of our repositories.
    ./snapshot_github.py daily --verbose

#### Run the Mailman scraper
   
    # The scraper connects to the public Mailman archives to download user activity.
    ./getactivity_mailman.py --verbose

    # It also runs a daily job to snapshot the number of subscribers and daily posts to each mailing list.
    # This accesses the subscriber roster, which requires a password set in an environment variable.
    # NOTE: This will record 0 posts-per-day unless the activity scraper has been run first!
    export MAILMAN_ADMIN=password1234...
    ./snapshot_mailman.py --verbose


## Hooking up to Heroku

The system is deployed on Heroku. `Procfile` declares the web frontend to be run. The Scheduler add-on runs each of the `scrape_*.py` scripts at regular intervals to keep the database up-to-date.

Installation:

* Get set up with the Heroku toolbelt
* Get your Heroku account authorized as a collaborator on the activityapi project
* Add the heroku remote and start pushing. Try to keep it in sync with Github!

    git remote add heroku git@heroku.com:activityapi.git 

## Interactive Mode

You can interact with the database and scrapers via Python's interactive terminal. For example:

    (%activityapi)$ DATABASE_URL=postgresql://localhost/zephod python
    Python 2.7.1 (r271:86832, Jun 16 2011, 16:59:05) 
    [GCC 4.2.1 (Based on Apple Inc. build 5658) (LLVM build 2335.15.00)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from lib.backend import model,Session

Pull snapshots from the database:

    >>> query = Session.query(model.SnapshotOfFacebook).order_by(model.SnapshotOfFacebook.timestamp.desc()).limit(5)
    >>> query[0].toJson()
    {'timestamp': '2013-02-20', 'likes': 2840}
    >>> 
    >>> from pprint import pprint
    >>> pprint( [ x.toJson() for x in query ] )
    [{'likes': 2840, 'timestamp': '2013-02-20'},
     {'likes': 2820, 'timestamp': '2013-02-18'},
     {'likes': 2812, 'timestamp': '2013-02-17'},
     {'likes': 2798, 'timestamp': '2013-02-16'},
     {'likes': 2775, 'timestamp': '2013-02-15'}]
