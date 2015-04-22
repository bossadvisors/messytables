from __future__ import absolute_import
import os
from io import open


def horror_fobj(name):
    fn = os.path.join(os.path.dirname(__file__), u'..', u'horror', name)
    return open(fn, u'rb')
