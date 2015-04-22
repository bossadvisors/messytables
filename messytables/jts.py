u'''
Convert a rowset to the json table schema
(http://www.dataprotocols.org/en/latest/json-table-schema.html)
'''

from __future__ import absolute_import
import messytables
import jsontableschema
from itertools import imap
from itertools import izip

MESSYTABLES_TO_JTS_MAPPING = {
    messytables.StringType: u'string',
    messytables.IntegerType: u'integer',
    messytables.FloatType: u'number',
    messytables.DecimalType: u'number',
    messytables.DateType: u'date',
    messytables.DateUtilType: u'date'
}


def celltype_as_string(celltype):
    return MESSYTABLES_TO_JTS_MAPPING[celltype.__class__]


def rowset_as_jts(rowset, headers=None, types=None):
    u''' Create a json table schema from a rowset
    '''
    _, headers = messytables.headers_guess(rowset.sample)
    types = list(imap(celltype_as_string, messytables.type_guess(rowset.sample)))

    return headers_and_typed_as_jts(headers, types)


def headers_and_typed_as_jts(headers, types):
    u''' Create a json table schema from headers and types as
    returned from :meth:`~messytables.headers.headers_guess`
    and :meth:`~messytables.types.type_guess`.
    '''
    j = jsontableschema.JSONTableSchema()

    for field_id, field_type in izip(headers, types):
        j.add_field(field_id=field_id,
                    label=field_id,
                    field_type=field_type)

    return j
