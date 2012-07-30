import views
from dash.frontend import app

app.add_url_rule('/', 'index', view_func=views.index, methods=('POST', 'GET'))
app.add_url_rule('/timestamps', 'timestamps', view_func=views.timestamps, methods=('POST', 'GET'))
