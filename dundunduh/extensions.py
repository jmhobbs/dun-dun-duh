# -*- coding: utf-8 -*-

from flask.ext.rq import RQ
from flask.ext.redis import Redis

rq = RQ()
redis = Redis()
