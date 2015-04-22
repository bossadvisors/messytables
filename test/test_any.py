# -*- coding: utf-8 -*-
from __future__ import absolute_import
import unittest

from . import horror_fobj
from nose.tools import assert_equal
from nose.plugins.skip import SkipTest
from messytables import (any_tableset, XLSTableSet, ZIPTableSet, PDFTableSet,
                         CSVTableSet, ODSTableSet,
                         ReadError)

suite = [{u'filename': u'simple.csv', u'tableset': CSVTableSet},
         {u'filename': u'simple.xls', u'tableset': XLSTableSet},
         {u'filename': u'simple.xlsx', u'tableset': XLSTableSet},
         {u'filename': u'simple.zip', u'tableset': ZIPTableSet},
         {u'filename': u'simple.ods', u'tableset': ODSTableSet},
         {u'filename': u'bian-anal-mca-2005-dols-eng-1011-0312-tab3.xlsm',
          u'tableset': XLSTableSet},
         ]

# Special handling for PDFTables - skip if not installed
try:
    import pdftables
except ImportError:
    got_pdftables = False
    suite.append({u"filename": u"simple.pdf", u"tableset": False})
else:
    from messytables import PDFTableSet
    got_pdftables = True
    suite.append({u"filename": u"simple.pdf", u"tableset": PDFTableSet})


def test_simple():
    for d in suite:
        yield check_no_filename, d
        yield check_filename, d


def check_no_filename(d):
    if not d[u'tableset']:
        raise SkipTest(u"Optional library not installed. Skipping")
    fh = horror_fobj(d[u'filename'])
    table_set = any_tableset(fh)
    assert isinstance(table_set, d[u'tableset']), type(table_set)


def check_filename(d):
    if not d[u'tableset']:
        raise SkipTest(u"Optional library not installed. Skipping")
    fh = horror_fobj(d[u'filename'])
    table_set = any_tableset(fh, extension=d[u'filename'], auto_detect=False)
    assert isinstance(table_set, d[u'tableset']), type(table_set)


class TestAny(unittest.TestCase):
    def test_xlsm(self):
        fh = horror_fobj(u'bian-anal-mca-2005-dols-eng-1011-0312-tab3.xlsm')
        table_set = any_tableset(fh, extension=u'xls')
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(62, len(data))

    def test_unknown(self):
        fh = horror_fobj(u'simple.unknown')
        self.assertRaises(ReadError,
                          lambda: any_tableset(fh, extension=u'unknown'))

    def test_scraperwiki_xlsx(self):
        fh = horror_fobj(u'sw_gen.xlsx')
        table_set = any_tableset(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(16, len(data))

    def test_libreoffice_xlsx(self):
        fh = horror_fobj(u'libreoffice.xlsx')
        table_set = any_tableset(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(0, len(data))
