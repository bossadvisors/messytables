from __future__ import absolute_import
import zipfile

import messytables


class ZIPTableSet(messytables.TableSet):
    u""" Reads TableSets from inside a ZIP file """

    def __init__(self, fileobj):
        u"""
        On error it will raise messytables.ReadError.
        """
        tables = []
        found = []
        z = zipfile.ZipFile(fileobj, u'r')
        try:
            for f in z.infolist():
                ext = None

                #ignore metadata folders added by Mac OS X
                if u'__MACOSX' in f.filename:
                    continue

                if u"." in f.filename:
                    ext = f.filename[f.filename.rindex(u".") + 1:]

                try:
                    filetables = messytables.any.any_tableset(
                        z.open(f), extension=ext)
                except ValueError, e:
                    found.append(f.filename + u": " + e.message)
                    continue

                tables.extend(filetables.tables)

            if len(tables) == 0:
                raise messytables.ReadError(u'''ZIP file has no recognized
                    tables (%s).''' % u', '.join(found))
        finally:
            z.close()
        
        self._tables = tables
