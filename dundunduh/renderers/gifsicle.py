# -*- coding: utf-8 -*-

import tempfile
import subprocess


def make_animated_gif(stream, images, delays):
    # gifsicle -m -O2 --dither --colors 128 --loopcount=forever -d25 0.gif 1.gif 2.gif 3.gif -d50 > out.gif
    command = ['gifsicle', '-m', '-O2', '--dither', '--colors', '128', '--loopcount=forever']

    temp_files = []
    i = 0
    for image in images:
        temp = tempfile.NamedTemporaryFile(suffix=".gif")
        image.save(temp)
        command.append('-d%d' % delays[i])
        command.append(temp.name)
        i += 1
        temp_files.append(temp)

    subprocess.call(command, stdout=stream)

    for temp in temp_files:
        temp.close()

    del temp_files
