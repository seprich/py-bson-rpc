# -*- coding: utf-8 -*-
'''
This module provides classes implementing different JSON-RPC 2.0 framing
options. Currently RFC-7464, Netstring and Frameless -framings are provided.

In case you need to use a different framing method, you can provide your own
implementor class for this library via settings.

The class you provide must have the following classmethods and behavior:
  * ``extract_message``
      .. code-block:: python

        @classmethod
        def extract_message(cls, raw_bytes)
            # Args:
            #    raw_bytes (bytes): 1 - N bytes from stream
            # Returns:
            #    bytes, bytes    (tuple of 2 byte strings)
            #       * (None, raw_bytes,) == raw_bytes contains only a partial
            #                               message.
            #       * (msg_bytes, rest,) == a complete message +
            #                               remaining bytes.
            # Raises:
            #    Any type of exception can be raised on a framing error.
            #    Library framework will coerce these into
            #    bsonrpc.exceptions.FramingError -exceptions however.
            return msg_bytes, rest_bytes
  * ``into_frame``
      .. code-block:: python

        @classmethod
        def into_frame(cls, message_bytes):
            # Args:
            #    message_bytes (bytes): 1 complete JSON message serialized
            #                           into bytes.
            # Returns:
            #    bytes
            #       == framed message.
            # Raises:
            #    Theoretically framing method could limit message size and
            #    message_bytes may be too long -> causing an error ->
            #    coerced to bsonrpc.exceptions.FramingError
            return framed_bytes
'''
__license__ = 'http://mozilla.org/MPL/2.0/'

from .exceptions import FramingError


class JSONFramingRFC7464(object):
    '''
    RFC-7464 framing.
    '''

    @classmethod
    def extract_message(cls, raw_bytes):
        if len(raw_bytes) < 2:
            return None, raw_bytes
        if raw_bytes[0] != 0x1e:
            raise FramingError(
                'Start marker is missing: %s' % raw_bytes)
        if b'\x0a' in raw_bytes:
            b_msg, rest = raw_bytes.split(b'\x0a', 1)
            return b_msg[1:], rest
        else:
            if b'\x1e' in raw_bytes[1:]:
                raise FramingError(
                    'End marker is missing: %s' % raw_bytes)
            return None, raw_bytes

    @classmethod
    def into_frame(cls, message_bytes):
        return b'\x1e' + message_bytes + b'\x0a'


class JSONFramingNetstring(object):
    '''
    Netstring framing.
    '''

    @classmethod
    def extract_message(cls, raw_bytes):
        if b':' not in raw_bytes:
            if len(raw_bytes) > 10:
                raise FramingError(
                    'Length information missing: %s' % raw_bytes)
            return None, raw_bytes
        msg_len, rest = raw_bytes.split(b':', 1)
        try:
            msg_len = int(msg_len)
        except ValueError:
            raise FramingError('Invalid length: %s' % raw_bytes)
        if msg_len < 0:
            raise FramingError('Negative length: %s' % raw_bytes)
        if len(rest) < msg_len + 1:
            return None, raw_bytes
        else:
            if rest[msg_len] != 44:
                raise FramingError(
                    'Missing correct end marker: %s' % raw_bytes)
            return rest[:msg_len], rest[(msg_len + 1):]

    @classmethod
    def into_frame(cls, message_bytes):
        msg_len = len(message_bytes)
        return bytes(str(msg_len), 'utf-8') + b':' + message_bytes + b','


class JSONFramingNone(object):
    '''
    Direct streaming without framing.
    '''

    @classmethod
    def extract_message(cls, raw_bytes):
        if len(raw_bytes) < 2:
            return None, raw_bytes
        if raw_bytes[0] != 123:
            raise FramingError(
                'Broken state. Expected JSON Object, got: %s' % raw_bytes)
        stack = [123]
        uniesc = 0
        poppers = {91: [93], 123: [125], 34: [34]}
        adders = {91: [34, 91, 123], 123: [34, 91, 123], 34: [92], 92: [117]}
        for idx in range(1, len(raw_bytes)):
            cbyte = raw_bytes[idx]
            if cbyte in poppers.get(stack[-1], []):
                stack.pop()
            elif cbyte in adders.get(stack[-1], []):
                stack.append(cbyte)
            elif stack[-1] == 92:
                stack.pop()
            elif stack[-1] == 117:
                uniesc += 1
                if uniesc >= 4:
                    stack = stack[:-2]
                    uniesc = 0
            if not stack:
                return raw_bytes[:idx + 1], raw_bytes[idx + 1:]
        return None, raw_bytes

    @classmethod
    def into_frame(cls, message_bytes):
        return message_bytes
