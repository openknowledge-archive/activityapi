import api
from dash.frontend import app

@app.route('/')
def homepage():
    return app.send_static_file('index.html')

app.add_url_rule('/api/', 'api', view_func=api.index, methods=('POST', 'GET'))
app.add_url_rule('/api/twitter', 'api.twitter', view_func=api.twitter)
app.add_url_rule('/api/timestamps', 'api.timestamps', view_func=api.timestamps)

