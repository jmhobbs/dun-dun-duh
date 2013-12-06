# -*- coding: utf-8 -*-

import os
import hashlib

from flask import request, redirect, url_for, render_template, send_from_directory, abort, jsonify
import flask.ext.rq
import rq.job

from PIL import Image

from .util import is_allowed_file, random_alphanumeric_string
from .queue import compose_animated_gif


def register_views(app):

    @app.route('/', methods=['GET', 'POST'])
    def upload_file():
        if request.method == 'POST':
            file = request.files['file']
            if file and is_allowed_file(file.filename):
                filename = random_alphanumeric_string(15) + '_' + hashlib.new('sha1', file.filename).hexdigest() + '.jpg'
                im = Image.open(file)
                w, h = im.size
                if w > app.config['LONGEST_SIDE'] or h > app.config['LONGEST_SIDE']:
                    if w > h:
                        new_size = (app.config['LONGEST_SIDE'], int(float(h) / w * app.config['LONGEST_SIDE']))
                    else:
                        new_size = (int(float(w) / h * app.config['LONGEST_SIDE']), app.config['LONGEST_SIDE'])
                    im = im.resize(new_size)
                size = im.size
                im.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "JPEG", quality=80)
                return redirect(url_for('crop_file', filename=filename, width=size[0], height=size[1]))
        return render_template('index.html')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/robots.txt')
    @app.route('/humans.txt')
    def root_level_static_files():
        return send_from_directory(app.static_folder, request.path[1:])

    @app.route('/crop/<filename>/<int:width>/<int:height>')
    def crop_file(filename, width, height):

        if width < height:
            size = max(10, int(width * .5))
            max_size = max(10, int(width * .75))
        else:
            size = max(10, int(height * .5))
            max_size = max(10, int(height * .75))

        x = int(float(width - size) / 2)
        y = int(float(height - size) / 2)

        return render_template('crop.html', filename=filename, size=size, max_size=max_size, x=x, y=y)

    @app.route('/compose/<filename>', methods=('POST',))
    def compose(filename):
        x = request.form.get('x', type=int)
        y = request.form.get('y', type=int)
        size = request.form.get('size', type=int)

        if x is None or y is None or size is None:
            abort(400)

        job = flask.ext.rq.get_queue('default').enqueue(compose_animated_gif, filename, x, y, size)

        return render_template('compose.html', job_id=job.id)

    @app.route('/job/status.json')
    def rq_job_status():
        if not request.args.get('id'):
            return jsonify({"error": True, "message": "No job id specified."}), 400

        job = rq.job.Job(request.args.get('id'), flask.ext.rq.get_connection())

        return jsonify({"error": False, "data": {"id": job.id, "status": job.status, "finished": job.is_finished, "failed": job.is_failed, "return_value": job.return_value}})