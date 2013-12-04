# -*- coding: utf-8 -*-

import os
from flask import Flask

from .config import BaseConfig
from .views import register_views
from .extensions import rq

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
