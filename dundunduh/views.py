# -*- coding: utf-8 -*-

import os
import hashlib

from flask import request, url_for, render_template, send_from_directory, abort, jsonify, session
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

        Should be overriden in production by an http server level rule.
        '''
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    #####################################################
    # App!
    @app.route('/')
    def index():
        upload_token = random_alphanumeric_string(10)
        session['upload_token'] = upload_token
        return render_template('index.html', upload_token=upload_token)

    @app.route('/upload', methods=('POST', 'HEAD'))
    def upload():
        '''
        Upload method for jQuery-upload XHR.  Uses session token to discourage spamming.
        '''
        response = {"error": False, "files": []}

        if request.method == 'POST':
            file = request.files.get('file')
            if request.form.get('upload_token') != session.get('upload_token', 'nopenopenope'):
                response["error"] = "Invalid upload token."
            elif not file:
                response["error"] = "No file uploaded."
            elif not is_allowed_file(file.filename):
                response["error"] = "Invalid file type."
            else:
                slug = random_alphanumeric_string(5) + hashlib.new('sha1', file.filename).hexdigest()[:5]
                filename = slug + '.jpg'

                im = Image.open(file)
                w, h = im.size
                if w > app.config['LONGEST_SIDE'] or h > app.config['LONGEST_SIDE']:
                    if w > h:
                        new_size = (app.config['LONGEST_SIDE'], int(float(h) / w * app.config['LONGEST_SIDE']))
                    else:
                        new_size = (int(float(w) / h * app.config['LONGEST_SIDE']), app.config['LONGEST_SIDE'])
                    im = im.resize(new_size)

                im.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "JPEG", quality=80)

                response['files'] = [{"name": file.filename, "id": slug, "redirect": url_for("crop_file", slug=slug, _external=True)}]

        response = jsonify(response)

        response.headers['Vary'] = 'Accept'

        # IE chokes on application/json in iframe uploads
        if 'HTTP_ACCEPT' in request.headers:
            if "application/json" in request.headers['HTTP_ACCEPT']:
                response.headers['Content-Type'] = 'application/json'
            else:
                response.headers['Content-Type'] = 'text/plain'

        return response

    @app.route('/crop/<slug>')
    def crop_file(slug):
        return render_template('crop.html', slug=slug, filename=slug + ".jpg")

    @app.route('/render/<slug>', methods=('POST',))
    def compose(slug):
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

        job = flask.ext.rq.get_queue('default').enqueue(compose_animated_gif, slug + ".jpg", center_x, center_y, size, frames)

        return render_template('compose.html', job_id=job.id)

    @app.route('/gif/<slug>')
    def view(slug):
        if app.config.get('UPLOAD_URL_FORMAT_STRING'):
            image_url = app.config.get('UPLOAD_URL_FORMAT_STRING') % {"filename": slug, "extension": ".gif"}
        else:
            image_url = url_for('uploaded_file', filename=slug + ".gif", _external=True)
        return render_template('view.html', image_url=image_url)

    @app.route('/job/status.json')
    def rq_job_status():
        if not request.args.get('id'):
            return jsonify({"error": True, "message": "No job id specified."}), 400

        job = rq.job.Job(request.args.get('id'), flask.ext.rq.get_connection())

        return jsonify({
            "error": False,
            "data": {
                "id": job.id,
                "status": job.status,
                "finished": job.is_finished,
                "failed": job.is_failed,
                "return_value": job.return_value
            }
        })
