Dashboard2
----------

Prerequisites:
 
    # Create a Postgres database and configure an environment variable:
    export DATABASE_URL=postgresql://user:pass@localhost/mydatabase 

Setup:

    # Install the dashboard requirements
    virtualenv env.dashboard
    . env.dashboard/bin/activate
    pip install -r requirements.txt
    # Start the server
    ./frontend.py

Execute scrapers:

    ./scrape_timestamp.py

In Production
-------------
The system is deployed on Heroku. `Procfile` declares the web frontend to be run. The Scheduler add-on runs each of the `scrape_*.py` scripts at regular intervals to keep the database up-to-date.
