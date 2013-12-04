# -*- coding: utf-8 -*-

import os
from PIL import Image

from flask import current_app, url_for

from ..renderers.gifsicle import make_animated_gif


def compose_animated_gif(filename, x, y, size):
    print 'compose', filename, (x, y), size

    center_point = (x + int(size * .5), y + int(size * .5))

    print 'center', center_point

    im = Image.open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
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
        if x2 >= w:
            print "x2 outside width by", x2 - w
            x1 = x1 - (x2 - w)
            x2 = w

        if y2 >= h:
            print "y2 outside height by", y2 - h
            y1 = y1 - (y2 - h)
            y2 = h

        if x1 < 0:
            print 'x1 outside 0 by', x1
            x2 = x2 + (-1 * x1)
            x1 = 0

        if y1 < 0:
            print 'y1 outside 0 by', y1
            y2 = y2 + (-1 * y1)
            y1 = 0

        frames.append((x1, y1, x2, y2))

    frames = list(reversed(frames))

    print frames

    _frames = []

    for i in xrange(0, 5):
        frame = im.crop(frames[i]).resize((peak_size, peak_size))
        _frames.append(frame.convert('P'))

    output_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], filename.replace('.jpg', '.gif'))

    with open(output_filename, 'wb') as handle:
            make_animated_gif(handle, _frames, (35, 35, 35, 35, 250))

    return {"filename": filename.replace(".jpg", ".gif"), "url": url_for('uploaded_file', filename=filename.replace('.jpg', '.gif'))}
