# -*- coding: utf-8 -*-

import os
import hashlib

from datetime import datetime, timedelta
import time
from pytz import timezone

from flask import request, url_for, render_template, send_from_directory, abort, jsonify, session
import flask.ext.rq
import rq.job
import json

from PIL import Image

from .util import is_allowed_file, random_alphanumeric_string
from .util.ip import extract_remote_ip_from_headers
from .queue import compose_animated_gif
from . import records


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

        ip = extract_remote_ip_from_headers(request.headers)
        if not ip:
            ip = request.remote_addr

        job = flask.ext.rq.get_queue('default').enqueue(compose_animated_gif, slug, center_x, center_y, size, frames, time.time(), ip)

        return render_template('compose.html', job_id=job.id)

    @app.route('/gif/<slug>')
    def view(slug):
        filename = slug + ".gif"
        if app.config.get('UPLOAD_URL_FORMAT_STRING'):
            image_url = app.config.get('UPLOAD_URL_FORMAT_STRING') % {"filename": filename}
        else:
            image_url = url_for('uploaded_file', filename=filename, _external=True)
        return render_template('view.html', image_url=image_url)

    @app.route('/recent')
    def recent():
        raise NotImplemented()

    @app.route('/stats')
    def stats():
        tz = timezone(app.config.get('TIMEZONE', 'UTC'))

        dt = datetime.fromtimestamp(time.time())
        dt = tz.localize(dt)

        averages_week = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,0,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(0,255,0,1)", "data": []}
            ]
        }

        for i in xrange(7):
            ndt = dt - timedelta(days=6 - i)
            averages_week['labels'].append(ndt.strftime('%a'))
            averages_week['datasets'][0]['data'].append(records.get_daily_average(ndt, 'total'))
            averages_week['datasets'][1]['data'].append(records.get_daily_average(ndt, 'wait'))
            averages_week['datasets'][2]['data'].append(records.get_daily_average(ndt, 'render'))
            averages_week['datasets'][3]['data'].append(records.get_daily_average(ndt, 'store'))

        averages_day = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,0,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(0,255,0,1)", "data": []}
            ]
        }

        for i in xrange(24):
            ndt = dt - timedelta(hours=23 - i)
            averages_day["labels"].append(ndt.strftime("%H:00"))
            averages_day['datasets'][0]['data'].append(records.get_hourly_average(ndt, 'total'))
            averages_day['datasets'][1]['data'].append(records.get_hourly_average(ndt, 'wait'))
            averages_day['datasets'][2]['data'].append(records.get_hourly_average(ndt, 'render'))
            averages_day['datasets'][3]['data'].append(records.get_hourly_average(ndt, 'store'))

        averages_hour = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,0,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(0,255,0,1)", "data": []}
            ]
        }

        for i in xrange(20):
            segment = (dt.minute / 5) * 5
            ndt = dt - timedelta(minutes=(dt.minute - segment) + ((19 - i) * 5))
            averages_hour["labels"].append(ndt.strftime("%H:%M"))
            averages_hour['datasets'][0]['data'].append(records.get_five_minute_segment_average(ndt, 'total'))
            averages_hour['datasets'][1]['data'].append(records.get_five_minute_segment_average(ndt, 'wait'))
            averages_hour['datasets'][2]['data'].append(records.get_five_minute_segment_average(ndt, 'render'))
            averages_hour['datasets'][3]['data'].append(records.get_five_minute_segment_average(ndt, 'store'))

        processed_week = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
            ]
        }

        for i in xrange(7):
            ndt = dt - timedelta(days=6 - i)
            processed_week['labels'].append(ndt.strftime('%a'))
            processed_week['datasets'][0]['data'].append(records.get_daily_created(ndt))
            processed_week['datasets'][1]['data'].append(records.get_daily_failed(ndt))

        processed_day = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
            ]
        }

        for i in xrange(24):
            ndt = dt - timedelta(hours=23 - i)
            processed_day['labels'].append(ndt.strftime('%H:00'))
            processed_day['datasets'][0]['data'].append(records.get_hourly_created(ndt))
            processed_day['datasets'][1]['data'].append(records.get_hourly_failed(ndt))

        processed_hour = {
            "labels": [],
            "datasets": [
                {"strokeColor": "rgba(0,0,255,1)", "data": []},
                {"strokeColor": "rgba(255,0,0,1)", "data": []},
            ]
        }

        for i in xrange(20):
            segment = (dt.minute / 5) * 5
            ndt = dt - timedelta(minutes=(dt.minute - segment) + ((19 - i) * 5))
            processed_hour['labels'].append(ndt.strftime('%H:%M'))
            processed_hour['datasets'][0]['data'].append(records.get_five_minute_segment_created(ndt))
            processed_hour['datasets'][1]['data'].append(records.get_five_minute_segment_failed(ndt))

        return render_template(
            "stats.html",
            all_time_created=records.get_all_time_created(),
            all_time_failed=records.get_all_time_failed(),
            all_time_average=records.get_all_time_average('total'),
            total_time_week=json.dumps(averages_week),
            total_time_one_day=json.dumps(averages_day),
            total_time_hour=json.dumps(averages_hour),
            processed_week=json.dumps(processed_week),
            processed_day=json.dumps(processed_day),
            processed_hour=json.dumps(processed_hour)
        )

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
