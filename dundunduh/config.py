# -*- coding: utf-8 -*-


class BaseConfig(object):
    ENV = 'PRODUCTION'

    DEBUG = False
    TESTING = False

    REDIS_URL = 'redis://localhost:6379/0'

    UPLOAD_DESTINATION = 'local'

    AWS_ACCESS_KEY = None
    AWS_SECRET_KEY = None
    S3_BUCKET = None

    # Max POST request size
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024  # 6MB

    # Size in pixels to crop images
    LONGEST_SIDE = 400


class TestConfig(BaseConfig):
    ENV = 'TESTING'

    TESTING = True
    CSRF_ENABLED = False

    REDIS_URL = 'redis://localhost:6379/15'
