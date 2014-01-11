# -*- coding: utf-8 -*-

import os

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket

import time

from PIL import Image

from flask import current_app, url_for

from ..renderers.gifsicle import make_animated_gif
from ..crop import build_crops
from ..records import create_gif, create_gif_failed


def compose_animated_gif(slug, x, y, size, frame_count, queue_time, ip="0.0.0.0"):
    try:
        return _do_compose_animated_gif(slug, x, y, size, frame_count, queue_time, ip)
    except Exception as e:
        create_gif_failed(queue_time)
        raise e


def _do_compose_animated_gif(slug, x, y, size, frame_count, queue_time, ip="0.0.0.0"):
    filename = slug + ".gif"
    still_filename = slug + ".jpg"

    start_rendering = time.time()

    im = Image.open(os.path.join(current_app.config['UPLOAD_FOLDER'], slug + ".jpg"))
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

    output_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    first_frame_still_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], still_filename)

    with open(output_filename, 'wb') as handle:
            make_animated_gif(handle, frames, times)

    with open(first_frame_still_filename, 'wb') as handle:
        frames[0].convert('RGB').save(handle, quality=80)

    done_rendering = time.time()

    if 's3' == current_app.config.get('UPLOAD_DESTINATION', 'local'):
        image_url = publishToS3(output_filename, filename, 'image/gif')
        still_image_url = publishToS3(first_frame_still_filename, still_filename, 'image/jpeg')
    else:
        image_url = url_for('uploaded_file', filename=filename)
        still_image_url = url_for('uploaded_file', filename=still_filename)

    done_storing = time.time()

    wait_duration = start_rendering - queue_time
    render_duration = done_rendering - start_rendering
    store_duration = done_storing - done_rendering
    total_queue_duration = done_storing - queue_time

    # Store it in Redis
    create_gif(slug, ip, queue_time, start_rendering, wait_duration, render_duration, store_duration, total_queue_duration)

    return {
        "filename": filename,
        "slug": slug,
        "view_url": url_for('view', slug=slug),
        "image_url": image_url,
        "still_image_url": still_image_url,
        "stats": {
            "wait": wait_duration,
            "render": render_duration,
            "store": store_duration,
            "total": total_queue_duration
        }
    }


def publishToS3(source_file, filename, content_type):
    connection = S3Connection(current_app.config['AWS_ACCESS_KEY'], current_app.config['AWS_SECRET_KEY'])
    bucket = Bucket(connection, current_app.config['S3_BUCKET'])

    # http://vedovini.net/2010/06/properly-uploading-files-to-amazon-s3/
    key = Key(bucket, filename)
    key.set_contents_from_filename(source_file, headers={'Content-Type': content_type, 'Cache-Control': 'max-age %d' % (3600 * 24 * 365)}, policy='public-read')

    if current_app.config.get('UPLOAD_URL_FORMAT_STRING'):
        return current_app.config.get('UPLOAD_URL_FORMAT_STRING') % {"filename": filename}
    else:
        return u'http://%s.s3.amazon.com/%s' % (current_app.config['S3_BUCKET'], filename)
