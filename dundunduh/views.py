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

    #####################################################
    # Util and static. Override these in nginx

    @app.route('/robots.txt')
    @app.route('/humans.txt')
    def root_level_static_files():
        return send_from_directory(app.static_folder, request.path[1:])

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        '''
        Static path for uploaded images.
        '''
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    #####################################################
    # App!

    @app.route('/', methods=['GET', 'POST'])
    def index():
        '''
        The first step in the process, file upload, resize, and storage.
        '''
        if request.method == 'POST':
            file = request.files['file']
            if file and is_allowed_file(file.filename):

                filename = random_alphanumeric_string(5) + hashlib.new('sha1', file.filename).hexdigest()[:5] + '.jpg'

                im = Image.open(file)
                w, h = im.size
                if w > app.config['LONGEST_SIDE'] or h > app.config['LONGEST_SIDE']:
                    if w > h:
                        new_size = (app.config['LONGEST_SIDE'], int(float(h) / w * app.config['LONGEST_SIDE']))
                    else:
                        new_size = (int(float(w) / h * app.config['LONGEST_SIDE']), app.config['LONGEST_SIDE'])
                    im = im.resize(new_size)

                im.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "JPEG", quality=80)

                return redirect(url_for('crop_file', filename=filename))
        return render_template('index.html')

    @app.route('/crop/<filename>')
    def crop_file(filename):
        return render_template('crop.html', filename=filename)

    @app.route('/render/<filename>', methods=('POST',))
    def compose(filename):
        x = request.form.get('x', type=int)
        y = request.form.get('y', type=int)
        size = request.form.get('size', type=int)

        if x is None or y is None or size is None:
            abort(400)

        # TODO: auto-choose frame count
        frames = 5

#        if frames < 3:
#            frames = 3
#        elif frames > 7:
#            frames = 7

        center_x = x + int(size * 0.5)
        center_y = y + int(size * 0.5)

        job = flask.ext.rq.get_queue('default').enqueue(compose_animated_gif, filename, center_x, center_y, size, frames)

        return render_template('compose.html', job_id=job.id)

    @app.route('/gif/<filename>')
    def view(filename):
        if app.config.get('UPLOAD_URL_FORMAT_STRING'):
            image_url = app.config.get('UPLOAD_URL_FORMAT_STRING') % {"filename": filename, "extension": ".gif"}
        else:
            image_url = url_for('uploaded_file', filename=filename + ".gif", _external=True)
        return render_template('view.html', image_url=image_url)

    @app.route('/job/status.json')
    def rq_job_status():
        if not request.args.get('id'):
            return jsonify({"error": True, "message": "No job id specified."}), 400

        job = rq.job.Job(request.args.get('id'), flask.ext.rq.get_connection())

        return jsonify({"error": False, "data": {"id": job.id, "status": job.status, "finished": job.is_finished, "failed": job.is_failed, "return_value": job.return_value}})
