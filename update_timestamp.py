#!/usr/bin/env python

import application
from application import db, Ts
from time import gmtime, strftime

timestring = strftime("%Y-%m-%d %H:%M:%S", gmtime())
t = Ts(timestring)
db.session.add(t)
db.session.commit()

