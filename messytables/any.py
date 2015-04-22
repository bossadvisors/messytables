from __future__ import absolute_import
from messytables import (ZIPTableSet, PDFTableSet, CSVTableSet, XLSTableSet,
                         HTMLTableSet, ODSTableSet)
import messytables
import re


MIMELOOKUP = {u'application/x-zip-compressed': u'ZIP',
              u'application/zip': u'ZIP',
              u'text/comma-separated-values': u'CSV',
              u'application/csv': u'CSV',
              u'text/csv': u'CSV',
              u'text/tab-separated-values': u'TAB',
              u'application/tsv': u'TAB',
              u'text/tsv': u'TAB',
              u'application/ms-excel': u'XLS',
              u'application/xls': u'XLS',
              u'application/vnd.ms-excel': u'XLS',
              u'application/octet-stream': u'XLS', # libmagic detects sw_gen as this on mac
                                                 # with text "Microsoft OOXML"
              u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': u'XLS',
              u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheetapplication/zip': u'XLS',
              u'text/html': u'HTML',
              u'application/xml': u'HTML', # XHTML is often served as application-xml
              u'application/pdf': u'PDF',
              u'text/plain': u'CSV',  # could be TAB.
              u'application/CDFV2-corrupt': u'XLS',
              u'application/vnd.oasis.opendocument.spreadsheet': u'ODS',
              u'application/x-vnd.oasis.opendocument.spreadsheet': u'ODS',
              }

def TABTableSet(fileobj):
    return CSVTableSet(fileobj, delimiter=u'\t')

parsers = {u'TAB': TABTableSet,
           u'ZIP': ZIPTableSet,
           u'XLS': XLSTableSet,
           u'HTML': HTMLTableSet,
           u'CSV': CSVTableSet,
           u'ODS': ODSTableSet,
           u'PDF': PDFTableSet}


def clean_ext(filename):
    u"""Takes a filename (or URL, or extension) and returns a better guess at
    the extension in question.
    >>> clean_ext("")
    ''
    >>> clean_ext("tsv")
    'tsv'
    >>> clean_ext("FILE.ZIP")
    'zip'
    >>> clean_ext("http://myserver.info/file.xlsx?download=True")
    'xlsx'
    """
    dot_ext = u'.' + filename
    matches = re.findall(u'\.(\w*)', dot_ext)
    return matches[-1].lower()


def get_mime(fileobj):
    import magic
    # Since we need to peek the start of the stream, make sure we can
    # seek back later. If not, slurp in the contents into a StringIO.
    fileobj = messytables.seekable_stream(fileobj)
    header = fileobj.read(4096)
    mimetype = magic.from_buffer(header, mime=True).decode(u'utf-8')
    fileobj.seek(0)
    if MIMELOOKUP.get(mimetype) == u'ZIP':
        # consider whether it's an Microsoft Office document
        if "[Content_Types].xml" in header:
            return u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    # There's an issue with vnd.ms-excel being returned from XLSX files, too.
    if mimetype == u'application/vnd.ms-excel' and header[:2] == 'PK':
        return u'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return mimetype


def guess_mime(mimetype):
    # now returns a clean 'extension' as a string, not a function to call.
    found = MIMELOOKUP.get(mimetype)
    if found:
        return found

    # But some aren't mimetyped due to being buggy but load fine!
    fuzzy_lookup = {u'Composite Document File V2 Document': u'XLS'}
    for candidate in fuzzy_lookup:
        if candidate in mimetype:
            return fuzzy_lookup[candidate]


def guess_ext(ext):
    # returns a clean extension as a string, not a function to call.
    lookup = {u'zip': u'ZIP',
              u'csv': u'CSV',
              u'tsv': u'TAB',
              u'xls': u'XLS',
              u'xlsx': u'XLS',
              u'htm': u'HTML',
              u'html': u'HTML',
              u'pdf': u'PDF',
              u'xlt': u'XLS',
                # obscure Excel extensions taken from
                # http://en.wikipedia.org/wiki/List_of_Microsoft_Office_filename_extensions
              u'xlm': u'XLS',
              u'xlsm': u'XLS',
              u'xltx': u'XLS',
              u'xltm': u'XLS',
              u'ods': u'ODS'}
    if ext in lookup:
        return lookup.get(ext, None)


def any_tableset(fileobj, mimetype=None, extension=u'', auto_detect=True):
    u"""Reads any supported table type according to a specified
    MIME type or file extension or automatically detecting the
    type.

    Best matching TableSet loaded with the fileobject is returned.
    Matching is done by looking at the type (e.g mimetype='text/csv'), then
    the file extension (e.g. extension='tsv'), then autodetecting the
    file format by using the magic library which looks at the first few
    bytes of the file BUT is often wrong. Consult the source for recognized
    MIME types and file extensions.

    On error it raises messytables.ReadError
    """

    short_ext = clean_ext(extension)
    # Auto-detect if the caller has offered no clue. (Because the
    # auto-detection routine is pretty poor.)
    error = []

    if mimetype is not None:
        attempt = guess_mime(mimetype)
        if attempt:
            return parsers[attempt](fileobj)
        else:
            error.append(
                u'Did not recognise MIME type given: "{mimetype}".'.format(
                    mimetype=mimetype))

    if short_ext is not u'':
        attempt = guess_ext(short_ext)
        if attempt:
            return parsers[attempt](fileobj)
        else:
            error.append(
                u'Did not recognise extension "{ext}" (given "{full})".'.format(
                    ext=short_ext, full=extension))

    if auto_detect:
        magic_mime = get_mime(fileobj)
        attempt = guess_mime(magic_mime)
        if attempt:
            return parsers[attempt](fileobj)
        else:
            error.append(
                u'Did not recognise detected MIME type: "{mimetype}".'.format(
                    mimetype=magic_mime))

    if error:
        raise messytables.ReadError(u'any: \n'.join(error))
    else:
        raise messytables.ReadError(u"any: Did not attempt any detection.")


class AnyTableSet(object):
    u'''Deprecated - use any_tableset instead.'''
    @staticmethod
    def from_fileobj(fileobj, mimetype=None, extension=None):
        return any_tableset(fileobj, mimetype=mimetype, extension=extension)
