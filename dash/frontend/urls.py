import api1
import json
from dash.frontend import app
from flask import request,make_response

@app.route('/')
def homepage():
    return app.send_static_file('index.html')

@app.route('/api/')
def api_no_version():
    data = { 
            'error': 'No API version supplied', 
            'v1': request.url_root+'api/1/',
            }
    return json.dumps(data)

def wrap(function):
    def out():
        callback = request.args.get('callback')
        response_text = json.dumps(function())
        if callback:
            response_text = '%s(%s);' % (callback,response_text)
        response = make_response(response_text)
        response.headers['content-type'] = 'application/json'
        return response
    return out

app.add_url_rule('/api/1/', 'api1.index', view_func=wrap(api1.index))

app.add_url_rule('/api/1/debug/request', 'api1.debug_request', view_func=wrap(api1.debug_request), methods=["GET","POST"])
app.add_url_rule('/api/1/debug/timestamps', 'api1.debug_timestamps', view_func=wrap(api1.debug_timestamps))

app.add_url_rule('/api/1/twitter/tweets', 'api1.twitter_tweets', view_func=wrap(api1.twitter_tweets))
app.add_url_rule('/api/1/twitter/ratelimit', 'api1.twitter_ratelimit', view_func=wrap(api1.twitter_ratelimit))
app.add_url_rule('/api/1/twitter/trends', 'api1.twitter_trends', view_func=wrap(api1.twitter_trends))
app.add_url_rule('/api/1/person/list', 'api1.person_list', view_func=wrap(api1.person_list))

app.add_url_rule('/api/1/person/opinion', 'api1.person_opinion', view_func=wrap(api1.person_opinion), methods=["POST"])
