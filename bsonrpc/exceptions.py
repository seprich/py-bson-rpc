'''
'''


class ClosedError(RuntimeError):
    '''
    Queue/Socket closed
    '''


class CodecError(RuntimeError):
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
