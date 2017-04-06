# -*- coding: utf-8 -*-
'''
'''
import asyncio
from asyncio import Queue

__license__ = 'http://mozilla.org/MPL/2.0/'


class ProtocolQueue(object):
    '''
    Duplex queue:
        - protocol -> data_received -> get
        - put -> transport.write
    '''

    def __init__(self, transport, codec):
        self._is_closed = False
        self._codec = codec
        self._transport = transport
        self._bbuffer = b''
        self._queue = Queue()

    def _close_transport(self):
        if self._transport and not self._transport.is_closing():
            self._transport.close()
        self._is_closed = True

    def _to_queue(self, bbuffer):
        b_msg, bbuffer = self._codec.extract_message(bbuffer)
        while b_msg is not None:
            try:
                self._queue.put(self._codec.loads(b_msg))
            except DecodingError as e:
                self._queue.put(e)
            b_msg, bbuffer = self._codec.extract_message(bbuffer)
        return bbuffer

    def data_received(self, data):
        try:
            self._bbuffer = self._to_queue(self._bbuffer + data)
        except Exception as e:
            self._queue.put(e)
            self._close_transport()

    @asyncio.coroutine
    def get(self):
        return yield from self._queue.get()

    def put(self, item):
        '''
        Put item to queue -> codec -> socket.

        :param item: Message object.
        :type item: dict, list or None
        '''
        if self._is_closed:
            raise BsonRpcError('Attempt to put items to closed queue.')
        if self._transport:
            if item is None:
                self._close_transport()
            else:
                msg_bytes = self._codec.into_frame(self._codec.dumps(item))
                self._transport.write(msg_bytes)

    def connection_lost(self, exc):
        if exc:
            self._queue.put(exc)
        self._queue.put(None)
        self._is_closed = True

    @property
    def is_closed(self):
        return self._is_closed

    def close(self):
        self._close_transport()