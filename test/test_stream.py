# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest
import urllib2, urllib, urlparse
import urllib2, urllib
import urllib2, urllib
import requests
import io

from . import horror_fobj
from nose.tools import assert_equal
import httpretty

from messytables import CSVTableSet, XLSTableSet


class StreamInputTest(unittest.TestCase):
    @httpretty.activate
    def test_http_csv(self):
        url = u'http://www.messytables.org/static/long.csv'
        httpretty.register_uri(
            httpretty.GET, url,
            body=horror_fobj(u'long.csv').read(),
            content_type=u"application/csv")
        fh = urllib2.urlopen(url)
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(4000, len(data))

    @httpretty.activate
    def test_http_csv_requests(self):
        url = u'http://www.messytables.org/static/long.csv'
        httpretty.register_uri(
            httpretty.GET, url,
            body=horror_fobj(u'long.csv').read(),
            content_type=u"application/csv")
        r = requests.get(url, stream=True)
        # no full support for non blocking version yet, use urllib2
        fh = io.BytesIO(r.raw.read())
        table_set = CSVTableSet(fh, encoding=u'utf-8')
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(4000, len(data))

    @httpretty.activate
    def test_http_csv_encoding(self):
        url = u'http://www.messytables.org/static/utf-16le_encoded.csv'
        httpretty.register_uri(
            httpretty.GET, url,
            body=horror_fobj(u'utf-16le_encoded.csv').read(),
            content_type=u"application/csv")
        fh = urllib2.urlopen(url)
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(328, len(data))

    @httpretty.activate
    def test_http_xls(self):
        url = u'http://www.messytables.org/static/simple.xls'
        httpretty.register_uri(
            httpretty.GET, url,
            body=horror_fobj(u'simple.xls').read(),
            content_type=u"application/ms-excel")
        fh = urllib2.urlopen(url)
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(7, len(data))

    @httpretty.activate
    def test_http_xlsx(self):
        url = u'http://www.messytables.org/static/simple.xlsx'
        httpretty.register_uri(
            httpretty.GET, url,
            body=horror_fobj(u'simple.xlsx').read(),
            content_type=u"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        fh = urllib2.urlopen(url)
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(7, len(data))
