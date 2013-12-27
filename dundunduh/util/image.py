# -*- coding: utf-8 -*-

from PIL import ImageFilter


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
