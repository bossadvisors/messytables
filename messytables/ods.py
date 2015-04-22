from __future__ import absolute_import
import io
import re
import zipfile

from lxml import etree

from messytables.core import RowSet, TableSet, Cell
from messytables.types import (StringType, DecimalType,
                               DateType)


ODS_TABLE_MATCH = re.compile(u".*?(<table:table.*?<\/.*?:table>).*?", re.MULTILINE)
ODS_TABLE_NAME = re.compile(u'.*?table:name=\"(.*?)\".*?')
ODS_ROW_MATCH = re.compile(u".*?(<table:table-row.*?<\/.*?:table-row>).*?", re.MULTILINE)

ODS_TYPES = {
    u'float': DecimalType(),
    u'date': DateType(None),
}

NAMESPACES = {
    u"dc": u"http://purl.org/dc/elements/1.1/",
    u"draw": u"urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    u"number": u"urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    u"office": u"urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    u"svg": u"urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0",
    u"table": u"urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    u"text": u"urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}

# We must wrap the XML fragments in a valid header otherwise iterparse will
# explode with certain (undefined) versions of libxml2.

ODS_HEADER = u"<wrapper {0}>"\
    .format(u" ".join( u'xmlns:{0}="{1}"'.format(k,v)
            for k,v in NAMESPACES.items()))
ODS_FOOTER = u"</wrapper>"


class ODSTableSet(TableSet):
    u"""
    A wrapper around ODS files. Because they are zipped and the info we want
    is in the zipped file as content.xml we must ensure that we either have
    a seekable object (local file) or that we retrieve all of the content from
    the remote URL.
    """

    def __init__(self, fileobj, window=None):
        u'''Initialize the object.

        :param fileobj: may be a file path or a file-like object. Note the
        file-like object *must* be in binary mode and must be seekable (it will
        get passed to zipfile).

        As a specific tip: urllib2.urlopen returns a file-like object that is
        not in file-like mode while urllib.urlopen *does*!

        To get a seekable file you *cannot* use
        messytables.core.seekable_stream as it does not support the full seek
        functionality.
        '''
        if hasattr(fileobj, u'read'):
            # wrap in a StringIO so we do not have hassle with seeks and
            # binary etc (see notes to __init__ above)
            # TODO: rather wasteful if in fact fileobj comes from disk
            fileobj = io.BytesIO(fileobj.read())

        self.window = window

        zf = zipfile.ZipFile(fileobj).open(u"content.xml")
        self.content = zf.read()
        zf.close()

    def make_tables(self):
        u"""
            Return the sheets in the workbook.

            A regex is used for this to avoid having to:

            1. load large the entire file into memory, or
            2. SAX parse the file more than once
        """
        sheets = [m.groups(0)[0]
                  for m in ODS_TABLE_MATCH.finditer(self.content.decode(u'utf-8'))]
        return [ODSRowSet(sheet, self.window) for sheet in sheets]


class ODSRowSet(RowSet):
    u""" ODS support for a single sheet in the ODS workbook. Unlike
    the CSV row set this is not a streaming operation. """

    def __init__(self, sheet, window=None):
        self.sheet = sheet

        self.name = u"Unknown"
        m = ODS_TABLE_NAME.match(self.sheet)
        if m:
            self.name = m.groups(0)[0]

        self.window = window or 1000
        super(ODSRowSet, self).__init__(typed=True)

    def raw(self, sample=False):
        u""" Iterate over all rows in this sheet. """
        rows = ODS_ROW_MATCH.findall(self.sheet)

        for row in rows:
            row_data = []

            block = u"{0}{1}{2}".format(ODS_HEADER, row, ODS_FOOTER).encode(u'utf-8')
            partial = io.BytesIO(block)

            for action, elem in etree.iterparse(partial, (u'end',)):
                if elem.tag == u'{urn:oasis:names:tc:opendocument:xmlns:table:1.0}table-cell':
                    cell_type = elem.attrib.get(u'urn:oasis:names:tc:opendocument:xmlns:office:1.0:value-type')
                    children = elem.getchildren()
                    if children:
                        c = Cell(children[0].text,
                                 type=ODS_TYPES.get(cell_type, StringType()))
                        row_data.append(c)

            if not row_data:
                raise StopIteration()

            del partial
            yield row_data
        del rows
