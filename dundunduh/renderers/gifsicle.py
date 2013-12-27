# -*- coding: utf-8 -*-

import tempfile
import subprocess


def make_animated_gif(stream, images, delays):
    # This command is not as optimized for size, but might yield better quality.
    command = ['gifsicle', '-m', '-O2', '--dither', '--loopcount=forever']
    #command = ['gifsicle', '-m', '-O2', '--dither', '--colors', '255', '--loopcount=forever']

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
