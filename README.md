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
    # with an extra roweach time it is run:
    ./scrape_timestamp.py

#### Run the Twitter scraper

    # The scraper connects to my account(z_cron) which maintains Twitter lists of all OKFN members.
    # You'll need to get the credentials and store them in environment variables.
    export TWITTER_CONSUMER_SECRET=b1946ac9...
    export TWITTER_ACCESS_TOKEN_SECRET=591785b...
    
    # You can then run the scraper:
    ./scrape_twitter.py

In Production
-------------
The system is deployed on Heroku. `Procfile` declares the web frontend to be run. The Scheduler add-on runs each of the `scrape_*.py` scripts at regular intervals to keep the database up-to-date.
