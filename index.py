import os
import random
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort
from werkzeug import secure_filename
from PIL import Image
from PIL import GifImagePlugin
import itertools
import struct

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ALPHABET_LEN = len(ALPHABET)

LONGEST_SIDE = 400

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


# https://github.com/GoogleCloudPlatform/appengine-mandelbrot-python/blob/master/mandelbrot_animation.py
def build_animated_gif(stream, images, delays):
    """Writes an animated GIF into a stream given an iterator of PIL.Images.

    See http://en.wikipedia.org/wiki/Graphics_Interchange_Format#Animated_GIF.
    """
    image = images[0]

    # Header
    stream.write("GIF89a")

    # Logical Screen Descriptor
    stream.write(struct.pack('<H', image.size[0]))
    stream.write(struct.pack('<H', image.size[1]))
    stream.write("\x87\x00\x00")

    # Palette
    stream.write(GifImagePlugin.getheader(image)[1])

    # Application Extension
    stream.write("\x21\xFF\x0B")
    stream.write("NETSCAPE2.0")
    stream.write("\x03\x01")
    stream.write(struct.pack('<H', 2 ** 16 - 1))
    stream.write('\x00')

    for i in xrange(1, len(images)):
        # Graphic Control Extension
        stream.write('\x21\xF9\x04')
        stream.write('\x08')
        stream.write(struct.pack('<H', delays[i]))
        stream.write('\x00\x00')

        data = GifImagePlugin.getdata(images[i])
        for d in data:
            stream.write(d)

    # GIF file terminator
    stream.write(";")


def random_prefix(length=10):
    prefix = []
    for i in xrange(0, length):
        prefix.append(ALPHABET[random.randrange(0, ALPHABET_LEN)])
    return ''.join(prefix)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = random_prefix() + '_' + secure_filename(file.filename).replace('.', '_') + '.jpg'
            im = Image.open(file)
            w, h = im.size
            if w > LONGEST_SIDE or h > LONGEST_SIDE:
                if w > h:
                    new_size = (LONGEST_SIDE, int(float(h) / w * LONGEST_SIDE))
                else:
                    new_size = (int(float(w) / h * LONGEST_SIDE), LONGEST_SIDE)
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

    return render_template('crop.html', **locals())


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
        frame.save(os.path.join(app.config['UPLOAD_FOLDER'], str(i) + '_' + filename), 'JPEG')
        _frames.append(frame.convert('P'))

    with open(os.path.join(app.config['UPLOAD_FOLDER'], filename + '.gif'), 'wb') as handle:
            build_animated_gif(handle, _frames, (25, 25, 25, 25, 100))

    return render_template('compose.html', filename=filename)

if __name__ == '__main__':
    app.run(port=5050, debug=True)
