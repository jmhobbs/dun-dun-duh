# -*- coding: utf-8 -*-

import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket

from PIL import Image

from flask import current_app, url_for

from ..renderers.gifsicle import make_animated_gif
from ..crop import build_crops


def compose_animated_gif(filename, x, y, size, frame_count):

    im = Image.open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    w, h = im.size

    final_size = min(w, h, current_app.config.get('LONGEST_SIDE', 400))

    crops = build_crops(w, h, x, y, size, frame_count)

    times = []
    frames = []

    for i in xrange(0, frame_count):
        frame = im.crop(crops[i]).resize((final_size, final_size), Image.ANTIALIAS)
        frames.append(frame.convert('P'))
        times.append(35)

    times[-1] = 250

    output_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], filename.replace('.jpg', '.gif'))

    with open(output_filename, 'wb') as handle:
            make_animated_gif(handle, frames, times)

    if 's3' == current_app.config.get('UPLOAD_DESTINATION', 'local'):
        image_url = publishToS3(output_filename, 'image/gif')
    else:
        image_url = url_for('uploaded_file', filename=filename.replace('.jpg', '.gif'))

    # TODO: Clean up source, save to Redis.

    return {
        "filename": filename.replace(".jpg", ".gif"),
        "view_url": url_for('view', filename=filename.replace('.jpg', '')),
        "image_url": image_url
    }


def publishToS3(filename, content_type):
    connection = S3Connection(current_app.config['AWS_ACCESS_KEY'], current_app.config['AWS_SECRET_KEY'])
    bucket = Bucket(connection, current_app.config['S3_BUCKET'])

    name = os.path.basename(filename)

    # http://vedovini.net/2010/06/properly-uploading-files-to-amazon-s3/
    key = Key(bucket, name)
    key.set_contents_from_filename(filename, headers={'Content-Type': content_type, 'Cache-Control': 'max-age %d' % (3600 * 24 * 365)}, policy='public-read')

    if current_app.config.get('UPLOAD_URL_FORMAT_STRING'):
        return current_app.config.get('UPLOAD_URL_FORMAT_STRING') % {"filename": filename, "extension": ".gif"}
    else:
        return u'http://%s.s3.amazon.com/%s' % (current_app.config['S3_BUCKET'], name)
