# -*- coding: utf-8 -*-

import os
import socket

from flask import Flask

from .config import BaseConfig
from .views import register_views
from .extensions import rq, redis

app = Flask(__name__)

##############################
# Load Config

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

app.config.from_object(BaseConfig)
app.config.from_envvar('CONFIG', silent=True)

app.debug = app.config.get('DEBUG', False)

##############################
# Attach Views

register_views(app)

##############################
# Init Extensions

rq.init_app(app)
redis.init_app(app)

##############################
# Configure Templating


@app.context_processor
def inject_globals():
    return dict(
        g_ENVIRONMENT=app.config.get('ENV'),
        g_HOSTNAME=socket.gethostname(),
        g_IS_PRODUCTION=('PRODUCTION' == app.config.get('ENV')),
        g_SERVER_NAME=app.config.get('SERVER_NAME'),
        g_GOOGLE_ANALYTICS_ID=app.config.get('GOOGLE_ANALYTICS_ID')
    )
