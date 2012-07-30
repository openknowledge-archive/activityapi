from flask import Flask

app = Flask('dash.frontend')
app.config.from_object('dash.frontend.settings')

import urls

