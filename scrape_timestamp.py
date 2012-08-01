#!/usr/bin/env python

from dash.backend import Session
from dash.backend.model import Timestamp
from time import gmtime, strftime

timestring = strftime("%Y-%m-%d %H:%M:%S", gmtime())
t = Timestamp(timestring)
Session.add(t)
Session.commit()


