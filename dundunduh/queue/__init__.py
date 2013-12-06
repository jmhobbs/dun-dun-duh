# -*- coding: utf-8 -*-

import os
from PIL import Image, ImageFilter

from flask import current_app, url_for

from ..renderers.gifsicle import make_animated_gif
from ..crop import build_crops


# HACK
# In PIL 1.1.7 the blur kernel is hard coded small, so we hack it
# http://aaronfay.ca/content/post/python-pil-and-gaussian-blur/
# https://bugs.launchpad.net/phatch/+bug/528702
class VariableGaussianBlur(ImageFilter.Filter):
    name = "GaussianBlur"

    def __init__(self, radius=2):
        self.radius = radius

    def filter(self, image):
        return image.gaussian_blur(self.radius)

BLUR_FILTER = VariableGaussianBlur(radius=10)


def compose_animated_gif(filename, x, y, size):

    im = Image.open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    w, h = im.size

    final_size = min(w, h, current_app.config.get('LONGEST_SIDE', 400))

    crops = build_crops(w, h, x, y, size, 5)

    frames = []

    for i in xrange(0, 5):
        frame = im.crop(crops[i]).resize((final_size, final_size))
        if i > 1:
            frame = frame.filter(VariableGaussianBlur(i * 0.5))
        frames.append(frame.convert('P'))

    output_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], filename.replace('.jpg', '.gif'))

    with open(output_filename, 'wb') as handle:
            make_animated_gif(handle, frames, (35, 35, 35, 35, 250))

    return {"filename": filename.replace(".jpg", ".gif"), "url": url_for('uploaded_file', filename=filename.replace('.jpg', '.gif'))}
