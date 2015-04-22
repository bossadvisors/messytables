class MessytablesError(Exception):
    u"""A generic error to inherit from"""


class ReadError(MessytablesError):
    u'''Error reading the file/stream in terms of the expected format.'''
    pass


class TableError(MessytablesError, LookupError):
    u"""Couldn't identify correct table."""
    pass

class NoSuchPropertyError(MessytablesError, KeyError):
    u"""The requested property doesn't exist"""
    pass
