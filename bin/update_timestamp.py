#!/usr/bin/env python

from time import gmtime, strftime
import json

outfile = 'timestamp.json'
data = {'now': strftime("%Y-%m-%d %H:%M:%S", gmtime())}

with open(outfile,'w') as f:
  json.dump(data,f)
