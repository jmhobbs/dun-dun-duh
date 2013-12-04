# -*- coding: utf-8 -*-

from PIL import GifImagePlugin
import struct


def make_animated_gif(stream, images, delays):
    '''
    Adapted from https://github.com/GoogleCloudPlatform/appengine-mandelbrot-python/blob/master/mandelbrot_animation.py
    '''
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
