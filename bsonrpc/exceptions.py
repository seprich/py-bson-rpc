# -*- coding: utf-8 -*-
'''
Exceptions used in this library. Those which are imported in
__init__.py (and mentioned in API docs) are meant for library
users, other exceptions may be best for internal use only.
'''
__license__ = 'http://mozilla.org/MPL/2.0/'


class BsonRpcError(RuntimeError):
    '''
    Base class for produced errors.
    '''


class CodecError(BsonRpcError):
    '''
    Common base for framing and codec errors.
    '''


class FramingError(CodecError):
    '''
    Typically irrecoverable errors in message framing/unframing.
    '''


class EncodingError(CodecError):
    '''
    Error at encoding message.
    '''


class DecodingError(CodecError):
    '''
    Error while decoding message.
    '''
