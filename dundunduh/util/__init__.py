# -*- coding: utf-8 -*-

import random

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
ALPHABET_LEN = len(ALPHABET)


def random_alphanumeric_string(length):
    prefix = []
    for i in xrange(0, length):
        prefix.append(ALPHABET[random.randrange(0, ALPHABET_LEN)])
    return ''.join(prefix)


ALLOWED_FILE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_FILE_EXTENSIONS
