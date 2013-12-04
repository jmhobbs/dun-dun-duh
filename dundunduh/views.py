# -*- coding: utf-8 -*-

import os
import hashlib

from flask import request, redirect, url_for, render_template, send_from_directory, abort
from PIL import Image

from .util import is_allowed_file, random_alphanumeric_string
from .renderers.gifsicle import make_animated_gif


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

        print 'compose', filename, (x, y), size

        center_point = (x + int(size * .5), y + int(size * .5))

        print 'center', center_point

        im = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        print 'image', im.size

        w, h = im.size

        if w > h:
            size_difference = w - size
            peak_size = w
        else:
            size_difference = h - size
            peak_size = h

        print "size difference", size_difference

        pixel_difference_per_frame = int(size_difference / 5.0)

        print "pixels change per frame", pixel_difference_per_frame

        frames = []

        for i in xrange(0, 5):
            frame_size = pixel_difference_per_frame * i + size
            x1 = int(center_point[0] - frame_size * .5)
            y1 = int(center_point[1] - frame_size * .5)

            x2 = int(center_point[0] + frame_size * .5)
            y2 = int(center_point[1] + frame_size * .5)

            # Push centerpoint inward if out of bounds
            if x1 < 0:
                x2 = x2 + (-1 * x1)
                x1 = 0

            if y1 < 0:
                y2 = y2 + (-1 * y1)
                y1 = 0

            frames.append((x1, y1, x2, y2))

        frames = list(reversed(frames))

        print frames

        _frames = []

        for i in xrange(0, 5):
            frame = im.crop(frames[i]).resize((peak_size, peak_size))
            _frames.append(frame.convert('P'))

        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename.replace('.jpg', '.gif')), 'wb') as handle:
                make_animated_gif(handle, _frames, (35, 35, 35, 35, 250))

        return render_template('compose.html', filename=filename)
