# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

from messytables import dateparser, Cell


class DateParserTest(unittest.TestCase):
    def test_date_regex(self):
        assert dateparser.is_date(u'2012 12 22')
        assert dateparser.is_date(u'2012/12/22')
        assert dateparser.is_date(u'2012-12-22')
        assert dateparser.is_date(u'22.12.2012')
        assert dateparser.is_date(u'12 12 22')
        assert dateparser.is_date(u'22 Dec 2012')
        assert dateparser.is_date(u'2012 12 22 13:17')
        assert dateparser.is_date(u'2012 12 22 T 13:17')


class CellReprTest(unittest.TestCase):
    def test_repr_ok(self):
        repr(Cell(value=u"\xa0"))
