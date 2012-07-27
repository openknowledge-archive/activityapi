import os
from flask import Flask
import json

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/time')
def get_time():
    with open('timestamp.json') as f:
      data = json.load(f)
      return '<pre>%s</pre>' % json.dumps(data,indent=4)

if __name__ == '__main__':
    import sys
    if '--debug' in sys.argv:
        app.debug = True
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
