# -*- coding: utf-8 -*-

import os
from flask import Flask
from .views import register_views

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.config['LONGEST_SIDE'] = 400

register_views(app)
