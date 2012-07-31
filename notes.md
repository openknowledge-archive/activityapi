Possible Sources
----------------

1. Mailman: /pipermail mbox downloads as mbox parsed messages.
3. Github: 
  Get repos: https://api.github.com/orgs/okfn/repos
  Then RSS all repos
4. RSS: simple scrape, feed reader. 
5. Twitter
6. Wordpress members list
7. Notebook posts

TODO
----
`wordpress_dump` to become top-level repo


Table Structure
---------------
CREATE TABLE tweets (
    id SERIAL NOT NULL, 
    tweet_id BIGINT, 
    timestamp TIMESTAMP WITHOUT TIME ZONE, 
    geo_x FLOAT, 
    geo_y FLOAT, 
    screen_name VARCHAR, 
    text VARCHAR, 
    PRIMARY KEY (id)
)
