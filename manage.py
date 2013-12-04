#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask.ext.script import Manager
from flask.ext.script.commands import Clean, ShowUrls

import flask.ext.rq

from dundunduh import app

manager = Manager(app)
manager.add_command("clean", Clean())
manager.add_command("urls", ShowUrls())


@manager.command
def work():
    # Preload queue libraries
    flask.ext.rq.get_worker('default').work()


if __name__ == "__main__":
    manager.run()
