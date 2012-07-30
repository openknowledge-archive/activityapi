from dash.backend import Session, model
from time import gmtime, strftime

def scrape_timestamp():
    timestring = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    t = model.Timestamp(timestring)
    Session.add(t)
    Session.commit()
