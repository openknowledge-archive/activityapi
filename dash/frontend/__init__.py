from flask import Flask

app = Flask('dash.frontend')
app.config.from_object('dash.frontend.settings')
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DB_CON

import urls

