from __future__ import absolute_import
import re
from itertools import izip

date_regex = re.compile(ur'''^\d{1,4}[-\/\.\s]\S+[-\/\.\s]\S+''')


def is_date(value):
    return date_regex.match(value)


def create_date_formats(day_first=True):
    u"""generate combinations of time and date
    formats with different delimeters
    """

    if day_first:
        date_formats = [u'dd/mm/yyyy', u'dd/mm/yy', u'yyyy/mm/dd']
        python_date_formats = [u'%d/%m/%Y', u'%d/%m/%y', u'%Y/%m/%d']
    else:
        date_formats = [u'mm/dd/yyyy', u'mm/dd/yy', u'yyyy/mm/dd']
        python_date_formats = [u'%m/%d/%Y', u'%m/%d/%y', u'%Y/%m/%d']

    date_formats += [
        # Things with words in
        u'dd/bb/yyyy', u'dd/bbb/yyyy'
    ]
    python_date_formats += [
        # Things with words in
        u'%d/%b/%Y', u'%d/%B/%Y'
    ]

    both_date_formats = list(izip(date_formats, python_date_formats))

    #time_formats = "hh:mmz hh:mm:ssz hh:mmtzd hh:mm:sstzd".split()
    time_formats = u"hh:mm:ssz hh:mm:ss hh:mm:sstzd".split()
    python_time_formats = u"%H:%M%Z %H:%M:%S %H:%M:%S%Z %H:%M%z %H:%M:%S%z".split()
    both_time_fromats = list(izip(time_formats, python_time_formats))

    #date_seperators = ["-","."," ","","/","\\"]
    date_seperators = [u"-", u".", u"/", u" "]

    all_date_formats = []

    for seperator in date_seperators:
        for date_format, python_date_format in both_date_formats:
            all_date_formats.append(
                (date_format.replace(u"/", seperator),
                 python_date_format.replace(u"/", seperator))
            )

    all_formats = {}

    for date_format, python_date_format in all_date_formats:
        all_formats[date_format] = python_date_format
        for time_format, python_time_format in both_time_fromats:

            all_formats[date_format + time_format] = \
                python_date_format + python_time_format

            all_formats[date_format + u"T" + time_format] =\
                python_date_format + u"T" + python_time_format

            all_formats[date_format + u" " + time_format] =\
                python_date_format + u" " + python_time_format
    return list(all_formats.values())

DATE_FORMATS = create_date_formats()
