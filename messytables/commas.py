from __future__ import absolute_import
import csv
import codecs
import chardet

from messytables.core import RowSet, TableSet, Cell
import messytables


class UTF8Recoder(object):
    u"""
    Iterator that reads an encoded stream and re-encodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        sample = f.read(2000)
        if not encoding:
            results = chardet.detect(sample)
            encoding = results[u'encoding']
            if not encoding:
                # Don't break, just try and load the data with
                # a semi-sane encoding
                encoding = u'utf-8'
        f.seek(0)
        self.reader = codecs.getreader(encoding)(f, u'ignore')

        # The reader only skips a BOM if the encoding isn't explicit about its
        # endianness (i.e. if encoding is UTF-16 a BOM is handled properly
        # and taken out, but if encoding is UTF-16LE a BOM is ignored).
        # However, if chardet sees a BOM it returns an encoding with the
        # endianness explicit, which results in the codecs stream leaving the
        # BOM in the stream. This is ridiculously dumb. For UTF-{16,32}{LE,BE}
        # encodings, check for a BOM and remove it if it's there.
        if encoding in (u"UTF-16LE", u"UTF-16BE", u"UTF-32LE", u"UTF-32BE"):
            bom = getattr(codecs, u"BOM_UTF" + encoding[4:6] +
                          u"_" + encoding[-2:], None)
            if bom:
                # Try to read the BOM, which is a byte sequence, from
                # the underlying stream. If all characters match, then
                # go on. Otherwise when a character doesn't match, seek
                # the stream back to the beginning and go on.
                for c in bom:
                    if f.read(1) != c:
                        f.seek(0)
                        break

    def __iter__(self):
        return self

    def next(self):
        line = self.reader.readline()
        if not line or line == u'\0':
            raise StopIteration
        result = line.encode(u"utf-8")
        return result


def to_unicode_or_bust(obj, encoding=u'utf-8'):
    if isinstance(obj, unicode):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


class CSVTableSet(TableSet):
    u""" A CSV table set. Since CSV is always just a single table,
    this is just a pass-through for the row set. """

    def __init__(self, fileobj, delimiter=None, quotechar=None, name=None,
                 encoding=None, window=None, doublequote=None,
                 lineterminator=None, skipinitialspace=None):
        self.fileobj = messytables.seekable_stream(fileobj)
        self.name = name or u'table'
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.encoding = encoding
        self.window = window
        self.doublequote = doublequote
        self.lineterminator = lineterminator
        self.skipinitialspace = skipinitialspace

    def make_tables(self):
        u""" Return the actual CSV table. """
        return [CSVRowSet(self.name, self.fileobj,
                          delimiter=self.delimiter,
                          quotechar=self.quotechar,
                          encoding=self.encoding,
                          window=self.window,
                          doublequote=self.doublequote,
                          lineterminator=self.lineterminator,
                          skipinitialspace=self.skipinitialspace)]


class CSVRowSet(RowSet):
    u""" A CSV row set is an iterator on a CSV file-like object
    (which can potentially be infinetly large). When loading,
    a sample is read and cached so you can run analysis on the
    fragment. """

    def __init__(self, name, fileobj, delimiter=None, quotechar=None,
                 encoding=u'utf-8', window=None, doublequote=None,
                 lineterminator=None, skipinitialspace=None):
        self.name = name
        seekable_fileobj = messytables.seekable_stream(fileobj)
        self.fileobj = UTF8Recoder(seekable_fileobj, encoding)
        def fake_ilines(fake_fileobj):
            for row in fake_fileobj:
                yield row.decode(u'utf-8')
        self.lines = fake_ilines(self.fileobj)
        self._sample = []
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.window = window or 1000
        self.doublequote = doublequote
        self.lineterminator = lineterminator
        self.skipinitialspace = skipinitialspace
        try:
            for i in xrange(self.window):
                self._sample.append(self.lines.next())
        except StopIteration:
            pass
        super(CSVRowSet, self).__init__()

    @property
    def _dialect(self):
        delim = u'\n'
        sample = delim.join(self._sample)
        try:
            dialect = csv.Sniffer().sniff(sample,
                delimiters=[u'\t', u',', u';', u'|'])
            dialect.lineterminator = delim
            dialect.doublequote = True
            return dialect
        except csv.Error:
            return csv.excel

    @property
    def _overrides(self):
        # some variables in the dialect can be overridden
        d = {}
        if self.delimiter:
            d[u'delimiter'] = self.delimiter
        if self.quotechar:
            d[u'quotechar'] = self.quotechar
        if self.doublequote:
            d[u'doublequote'] = self.doublequote
        if self.lineterminator:
            d[u'lineterminator'] = self.lineterminator
        if self.skipinitialspace is not None:
            d[u'skipinitialspace'] = self.skipinitialspace
        return d

    def raw(self, sample=False):
        def rows():
            for line in self._sample:
                yield line
            if not sample:
                for line in self.lines:
                    yield line

        # Fix the maximum field size to something a little larger
        csv.field_size_limit(256000)

        try:
            for row in csv.reader(rows(),
                    dialect=self._dialect, **self._overrides):
                yield [Cell(to_unicode_or_bust(c)) for c in row]
        except csv.Error, err:
            if u'newline inside string' in unicode(err) and sample:
                pass
            elif u'line contains NULL byte' in unicode(err):
                pass
            else:
                raise messytables.ReadError(u'Error reading CSV: %r, %r', err, list(rows())[0][:100])
