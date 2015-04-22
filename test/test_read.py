# -*- coding: utf-8 -*-
from __future__ import with_statement
from __future__ import absolute_import
import unittest

from . import horror_fobj
from nose.plugins.attrib import attr
from nose.tools import assert_equal
from nose.plugins.skip import SkipTest
from itertools import imap

try:
    # Python 2.6 doesn't provide these functions
    from nose.tools import assert_is_instance, assert_greater_equal
except ImportError:
    from .shim26 import assert_is_instance, assert_greater_equal

from messytables import (CSVTableSet, StringType, HTMLTableSet,
                         ZIPTableSet, XLSTableSet, XLSXTableSet, PDFTableSet,
                         ODSTableSet, headers_guess, headers_processor,
                         offset_processor, DateType, FloatType,
                         IntegerType, BoolType, rowset_as_jts,
                         types_processor, type_guess, ReadError,
                         null_processor)
import datetime


class ReadCsvTest(unittest.TestCase):
    def test_read_simple_csv(self):
        fh = horror_fobj(u'simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'date')
        assert_equal(row[1].value, u'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())

    def test_read_complex_csv(self):
        fh = horror_fobj(u'complex.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(4, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'date')
        assert_equal(row[1].value, u'another date')
        assert_equal(row[2].value, u'temperature')
        assert_equal(row[3].value, u'place')

        for row in list(row_set):
            assert_equal(4, len(row))
            assert_equal(row[0].type, StringType())

    def test_overriding_sniffed(self):
        # semicolon separated values
        fh = horror_fobj(u'simple.csv')
        table_set = CSVTableSet(fh, delimiter=u";")
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(len(row), 1)

    def test_read_head_padding_csv(self):
        fh = horror_fobj(u'weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert 11 == len(headers), headers
        assert_equal(u'1985', headers[1].strip())
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        for row in row_set:
            assert_equal(11, len(row))
        value = data[1][0].value.strip()
        assert value == u'Gefäßchirurgie', value

    def test_read_head_offset_csv(self):
        fh = horror_fobj(u'simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert_equal(offset, 0)
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        assert_equal(int(data[0][1].value), 1)
        data = list(row_set)
        assert_equal(int(data[0][1].value), 1)

    @attr(u"slow")
    def test_read_type_guess_simple(self):
        fh = horror_fobj(u'simple.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        types = type_guess(row_set.sample)
        expected_types = [DateType(u"%Y-%m-%d"), IntegerType(), StringType()]
        assert_equal(types, expected_types)

        row_set.register_processor(types_processor(types))
        data = list(row_set)
        header_types = [c.type for c in data[0]]
        assert_equal(header_types, [StringType()] * 3)
        row_types = [c.type for c in data[2]]
        assert_equal(expected_types, row_types)

    def test_apply_null_values(self):
        fh = horror_fobj(u'null.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        types = type_guess(row_set.sample, strict=True)
        expected_types = [IntegerType(), StringType(), BoolType(),
                          StringType()]
        assert_equal(types, expected_types)

        row_set.register_processor(types_processor(types))
        data = list(row_set)
        # treat null as non empty text and 0 as non empty integer
        assert [x.empty for x in data[0]] == [False, False, False, False]
        assert [x.empty for x in data[1]] == [False, False, False, False]
        assert [x.empty for x in data[2]] == [False, False, True, True]
        assert [x.empty for x in data[3]] == [False, False, False, False]
        assert [x.empty for x in data[4]] == [False, False, False, True]
        assert [x.empty for x in data[5]] == [False, False, False, True]

        # we expect None for Integers and "" for empty strings in CSV
        assert [x.value for x in data[2]] == [3, u"null", None, u""], data[2]

    def test_null_process(self):
        fh = horror_fobj(u'null.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        row_set.register_processor(null_processor([u'null']))
        data = list(row_set)

        nones = [[x.value is None for x in row] for row in data]
        assert_equal(nones[0], [False, True, False, False])
        assert_equal(nones[1], [False, False, False, True])
        assert_equal(nones[2], [False, True, False, False])

        types = type_guess(row_set.sample, strict=True)
        expected_types = [IntegerType(), BoolType(), BoolType(),
                          BoolType()]
        assert_equal(types, expected_types)

        row_set.register_processor(types_processor(types))

        # after applying the types, '' should become None for int columns
        data = list(row_set)
        nones = [[x.value is None for x in row] for row in data]
        assert_equal(nones[0], [False, True, False, False])
        assert_equal(nones[1], [False, False, False, True])
        assert_equal(nones[2], [False, True, True, True])

    def test_read_encoded_csv(self):
        fh = horror_fobj(u'utf-16le_encoded.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(328, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[1].value, u'Organisation_name')

    def test_long_csv(self):
        fh = horror_fobj(u'long.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(4000, len(data))

    def test_small_csv(self):
        fh = horror_fobj(u'small.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        data = list(row_set)
        assert_equal(1, len(data))

    def test_skip_initials(self):
        def rows(skip_policy):
            fh = horror_fobj(u'skip_initials.csv')
            table_set = CSVTableSet(fh,
                                    skipinitialspace=skip_policy)
            row_set = table_set.tables[0]
            return row_set

        second = lambda r: r[1].value

        assert u"goodbye" in list(imap(second, rows(True)))
        assert u"    goodbye" in list(imap(second, rows(False)))

    def test_guess_headers(self):
        fh = horror_fobj(u'weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set)
        assert u'Frauenheilkunde' in data[9][0].value, data[9][0].value

        fh = horror_fobj(u'weird_head_padding.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        row_set.register_processor(headers_processor([u'foo', u'bar']))
        data = list(row_set)
        assert u'foo' in data[12][0].column, data[12][0]
        assert u'Chirurgie' in data[12][0].value, data[12][0].value

    def test_read_encoded_characters_csv(self):
        fh = horror_fobj(u'characters.csv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        row_set.register_processor(headers_processor(headers))
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set)
        assert_equal(382, len(data))
        assert_equal(data[0][2].value, u'雲嘉南濱海國家風景區管理處')
        assert_equal(data[-1][2].value, u'沈光文紀念廳')


class ReadZipTest(unittest.TestCase):
    def test_read_simple_zip(self):
        fh = horror_fobj(u'simple.zip')
        table_set = ZIPTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'date')
        assert_equal(row[1].value, u'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())


class ReadTsvTest(unittest.TestCase):
    def test_read_simple_tsv(self):
        fh = horror_fobj(u'example.tsv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(141, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'hour')
        assert_equal(row[1].value, u'expr1_0_imp')
        for row in list(row_set):
            assert_equal(17, len(row))
            assert_equal(row[0].type, StringType())


class ReadSsvTest(unittest.TestCase):
    def test_read_simple_ssv(self):
        # semicolon separated values
        fh = horror_fobj(u'simple.ssv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(7, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'date')
        assert_equal(row[1].value, u'temperature')

        for row in list(row_set):
            assert_equal(3, len(row))
            assert_equal(row[0].type, StringType())


class ReadPsvTest(unittest.TestCase):
    def test_read_simple_psv(self):
        # pipe/vertical bar ("|") separated values
        fh = horror_fobj(u'simple.psv')
        table_set = CSVTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(29, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'Year')
        assert_equal(row[1].value, u'New dwellings')

        for row in list(row_set):
            assert_equal(6, len(row))
            assert_equal(row[0].type, StringType())


class ReadODSTest(unittest.TestCase):
    def test_read_simple_ods(self):
        fh = horror_fobj(u'simple.ods')
        table_set = ODSTableSet(fh)
        assert_equal(1, len(table_set.tables))
        row_set = table_set.tables[0]
        row = list(row_set.sample)[0]
        assert_equal(row[0].value, u'Name')
        assert_equal(row[1].value, u'Age')
        assert_equal(row[2].value, u'When')
        total = 4
        for row in row_set.sample:
            total = total - 1
            assert 3 == len(row), row
        assert_equal(total, 0)

    @attr(u"slow")
    def test_read_large_ods(self):
        fh = horror_fobj(u'large.ods')
        table_set = ODSTableSet(fh)
        assert_equal(6, len(table_set.tables))
        row_set = table_set.tables[0]
        row = row_set.raw().next()
        assert len(row) == 5, len(row)
        for row in row_set.sample:
            assert len(row) == 5, len(row)

    def test_annotated_ods(self):
        fh = horror_fobj(u'annotated.ods')
        table_set = ODSTableSet(fh)
        assert_equal(4, len(table_set.tables))
        row_set = table_set.tables[0]
        for row in row_set.sample:
            assert len(row) == 1, len(row)

        row_set = table_set.tables[1]
        l = len(list(row_set.sample))
        assert 87 == l, l


class XlsxBackwardsCompatibilityTest(unittest.TestCase):
    def test_that_xlsx_is_handled_by_xls_table_set(self):
        u"""
        Should emit a DeprecationWarning.
        """
        fh = horror_fobj(u'simple.xlsx')
        assert_is_instance(XLSXTableSet(fh), XLSTableSet)


class ReadXlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.large_xlsx_table_set = XLSTableSet(   # TODO
            horror_fobj(u'large.xlsx'))

    def test_read_simple_xls(self):
        fh = horror_fobj(u'simple.xls')
        table_set = XLSTableSet(fh)
        assert_equal(1, len(table_set.tables))
        row_set = table_set.tables[0]
        first_row = list(row_set.sample)[0]
        third_row = list(row_set.sample)[2]

        assert_is_instance(first_row[0].value, unicode)
        assert_is_instance(first_row[1].value, unicode)
        assert_is_instance(first_row[2].value, unicode)

        assert_is_instance(third_row[0].value, datetime.datetime)
        assert_is_instance(third_row[1].value, float)
        assert_is_instance(third_row[2].value, unicode)

        assert_equal(first_row[0].value, u'date')
        assert_equal(first_row[1].value, u'temperature')
        assert_equal(first_row[2].value, u'place')

        assert_equal(third_row[0].value, datetime.datetime(2011, 1, 2, 0, 0))
        assert_equal(third_row[1].value, -1)
        assert_equal(third_row[2].value, u'Galway')

        for row in list(row_set):
            assert 3 == len(row), row

    # Right now we can't read even passwordless encrypted files - in future
    # would be good to be able to.
    def test_attempt_read_encrypted_no_password_xls(self):
        fh = horror_fobj(u'encrypted_no_password.xls')
        errmsg = u"Can't read Excel file: XLRDError('Workbook is encrypted',)"
        try:
            XLSTableSet(fh)
        except ReadError, e:
            assert e.args[0] == errmsg
        else:
            assert False, u"Did not raise Read Error"

    def test_read_head_offset_excel(self):
        fh = horror_fobj(u'simple.xls')
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        offset, headers = headers_guess(row_set.sample)
        assert_equal(offset, 0)
        row_set.register_processor(offset_processor(offset + 1))
        data = list(row_set.sample)
        assert_equal(int(data[0][1].value), 1)
        data = list(row_set)
        assert_equal(int(data[0][1].value), 1)

    def test_read_simple_xlsx(self):
        fh = horror_fobj(u'simple.xlsx')
        table_set = XLSTableSet(fh)
        assert_equal(1, len(table_set.tables))
        row_set = table_set.tables[0]
        first_row = list(row_set.sample)[0]
        third_row = list(row_set.sample)[2]

        assert_is_instance(first_row[0].value, unicode)
        assert_is_instance(first_row[1].value, unicode)
        assert_is_instance(first_row[2].value, unicode)

        assert_is_instance(third_row[0].value, datetime.datetime)
        assert_is_instance(third_row[1].value, float)
        assert_is_instance(third_row[2].value, unicode)

        assert_equal(first_row[0].value, u'date')
        assert_equal(first_row[1].value, u'temperature')
        assert_equal(first_row[2].value, u'place')

        assert_equal(third_row[0].value, datetime.datetime(2011, 1, 2, 0, 0))
        assert_equal(third_row[1].value, -1.0)
        assert_equal(third_row[2].value, u'Galway')

        for row in list(row_set):
            assert 3 == len(row), row

    def test_large_file_report_sheet_has_11_cols_52_rows(self):
        table = self.large_xlsx_table_set[u'Report']
        num_rows = len(list(table))
        num_cols = len(list(table)[0])

        assert_equal(52, num_rows)
        assert_equal(11, num_cols)
        num_cells = sum(len(row) for row in table)
        assert_equal(num_rows * num_cols, num_cells)

    def test_large_file_data_sheet_has_11_cols_8547_rows(self):
        table = self.large_xlsx_table_set[u'data']
        num_rows = len(list(table))
        num_cols = len(list(table)[0])

        assert_equal(8547, num_rows)
        assert_equal(11, num_cols)
        num_cells = sum(len(row) for row in table)
        assert_equal(num_rows * num_cols, num_cells)

    def test_large_file_criteria_sheet_has_5_cols_12_rows(self):
        table = self.large_xlsx_table_set[u'criteria']
        num_rows = len(list(table))
        num_cols = len(list(table)[0])

        assert_equal(5, num_cols)
        assert_equal(12, num_rows)
        num_cells = sum(len(row) for row in table)
        assert_equal(num_rows * num_cols, num_cells)

    def test_read_type_know_simple(self):
        fh = horror_fobj(u'simple.xls')
        table_set = XLSTableSet(fh)
        row_set = table_set.tables[0]
        row = list(row_set.sample)[1]
        types = [c.type for c in row]
        assert_equal(types, [DateType(None), FloatType(), StringType()])

    def test_bad_first_sheet(self):
        # First sheet appears to have no cells
        fh = horror_fobj(u'problematic_first_sheet.xls')
        table_set = XLSTableSet(fh)
        tables = table_set.tables
        assert_equal(0, len(list(tables[0].sample)))
        assert_equal(1000, len(list(tables[1].sample)))


class ReadHtmlTest(unittest.TestCase):
    def test_read_real_html(self):
        fh = horror_fobj(u'html.html')
        table_set = HTMLTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(200, len(list(row_set)))
        row = list(row_set.sample)[0]
        assert_equal(row[0].value.strip(), u'HDI Rank')
        assert_equal(row[1].value.strip(), u'Country')
        assert_equal(row[4].value.strip(), u'2010')

    def test_invisible_text_html(self):
        fh = horror_fobj(u'invisible_text.html')
        table_set = HTMLTableSet(fh)
        row_set = table_set.tables[0]
        assert_equal(4, len(list(row_set)))
        row = list(row_set.sample)[1]
        assert_equal(row[5].value.strip(), u'1 July 1879')

    def test_read_span_html(self):
        fh = horror_fobj(u'rowcolspan.html')
        table_set = HTMLTableSet(fh)
        row_set = table_set.tables[0]

        magic = {}
        for y, row in enumerate(row_set):
            for x, cell in enumerate(row):
                magic[(x, y)] = cell.value

        tests = {(0, 0): u'05',
                 (0, 2): u'25',
                 (0, 3): u'',
                 (1, 3): u'36',
                 (1, 6): u'66',
                 (4, 7): u'79',
                 (4, 8): u'89'}

        for test in tests:
            assert_equal(magic[test], tests[test])

    def test_that_outer_table_contains_nothing(self):
        fh = horror_fobj(u'complex.html')
        tables = {}
        for table in HTMLTableSet(fh).tables:
            tables[table.name] = table

        # outer_table should contain no meaningful data
        outer_table = list(tables[u'Table 2 of 2'])
        assert_equal(len(outer_table), 1)
        assert_equal(len(outer_table[0]), 1)
        assert_equal(outer_table[0][0].value.
                     replace(u" ", u"").
                     replace(u"\n", u""),
                     u"headfootbody")

    def test_that_inner_table_contains_data(self):
        fh = horror_fobj(u'complex.html')
        tables = {}
        for table in HTMLTableSet(fh).tables:
            tables[table.name] = table

        inner_table = tables[u'Table 1 of 2']
        cell_values = []
        for row in inner_table:
            for cell in row:
                cell_values.append(cell.value)
        assert_equal([u'head', u'body', u'foot'], cell_values)

    def test_rowset_as_schema(self):
        from io import BytesIO as sio
        ts = CSVTableSet(sio('''name,dob\nmk,2012-01-02\n'''))
        rs = ts.tables[0]
        jts = rowset_as_jts(rs).as_dict()
        assert_equal(jts[u'fields'], [
            {u'type': u'string', u'id': u'name', u'label': u'name'},
            {u'type': u'date', u'id': u'dob', u'label': u'dob'}])

    def test_html_table_name(self):
        fh = horror_fobj(u'html.html')
        table_set = HTMLTableSet(fh)
        assert_equal(u'Table 1 of 3', table_set.tables[0].name)
        assert_equal(u'Table 2 of 3', table_set.tables[1].name)
        assert_equal(u'Table 3 of 3', table_set.tables[2].name)


class ReadPdfTest(unittest.TestCase):
    def setUp(self):
        with horror_fobj(u'simple.pdf') as fh:
            try:
                PDFTableSet(fh)
            except ImportError:
                # Optional library isn't installed. Skip the tests.
                raise SkipTest(u"pdftables is not installed, skipping PDF tests")


    def test_read_simple_pdf(self):
        with horror_fobj(u'simple.pdf') as fh:
            table_set = PDFTableSet(fh)

        assert_equal(1, len(list(table_set.tables)))

        (table,) = table_set.tables
        rows = list(table)

        assert_greater_equal(len(rows), 1)

    def test_pdf_names(self):
        with horror_fobj(u'simple.pdf') as fh:
            table_set = PDFTableSet(fh)
        assert_equal(u'Table 1 of 1 on page 1 of 1',
                     table_set.tables[0].name)
