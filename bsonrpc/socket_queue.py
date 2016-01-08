# -*- coding: utf-8 -*-
'''
JSON & BSON codecs and the SocketQueue class which uses them.
'''
from .concurrent import new_queue, spawn
from .exceptions import (
    ClosedError, CodecError, DecodingError, EncodingError, FramingError)

from queue import Empty
from struct import unpack


class BSONCodec(object):
    '''
    Encode/Decode message to/from BSON format.

    Pros:
      * Explicit type for binary data
          * No string piggypacking.
          * No size penalties.
      * Explicit type for datetime.
    Cons:
      * No top-level arrays -> no batch support.
    '''

    def __init__(self):
        # NOTE: From pymongo, not the `bson` 3rd party lib.
        import bson
        self._loads = bson.BSON.decode
        self._dumps = bson.BSON.encode

    def loads(self, b_msg):
        try:
            return self._loads(b_msg)
        except Exception as e:
            raise DecodingError(e)

    def dumps(self, msg):
        try:
            return self._dumps(msg)
        except Exception as e:
            raise EncodingError(e)

    def extract_message(self, raw_bytes):
        rb_len = len(raw_bytes)
        if rb_len < 4:
            return None, raw_bytes
        try:
            msg_len = unpack('<i', raw_bytes[:4])[0]
            if rb_len < msg_len:
                return None, raw_bytes
            else:
                return raw_bytes[:msg_len], raw_bytes[msg_len:]
        except Exception as e:
            raise FramingError(e)

    def into_frame(self, message_bytes):
        return message_bytes


class JSONCodec(object):
    '''
    Encode/Decode messages to/from JSON format.
    '''

    def __init__(self, extractor, framer):
        import json
        self._loads = json.loads
        self._dumps = json.dumps
        self._extractor = extractor
        self._framer = framer

    def loads(self, b_msg):
        try:
            return self._loads(b_msg.decode('utf-8'))
        except Exception as e:
            raise DecodingError(e)

    def dumps(self, msg):
        try:
            return bytes(
                self._dumps(msg, separators=(',', ':'), sort_keys=True),
                'utf-8')
        except Exception as e:
            raise EncodingError(e)

    def extract_message(self, raw_bytes):
        try:
            return self._extractor(raw_bytes)
        except Exception as e:
            raise FramingError(e)

    def into_frame(self, message_bytes):
        try:
            return self._framer(message_bytes)
        except Exception as e:
            raise FramingError(e)


class SocketQueue(object):
    '''
    SocketQueue is a duplex Queue connected to a given socket and
    internally takes care of the conversion chain:

        socket <-> raw-binary <-> codec <-> python data objects <-> queue
    '''

    BUFSIZE = 4096

    def __init__(self, socket, codec, threading_model):
        '''
        :param socket: Socket connected to rpc peer node.
        :type socket: socket.socket
        :param codec: Codec converting python data to/from binary data
        :type codec: BSONCodec or JSONCodec
        :param threading_model: Threading model
        :type threading_model: bsonrpc.options.ThreadingModel.GEVENT or
                               bsonrpc.options.ThreadingModel.THREADS
        '''
        self.socket = socket
        self.codec = codec
        self.from_socket_queue = new_queue(threading_model)
        self.to_socket_queue = new_queue(threading_model)
        self._closed = False
        self._run_sender = True
        self._run_receiver = True
        self._drained = False
        spawn(threading_model, self._sender)
        spawn(threading_model, self._receiver)

    @property
    def is_closed(self):
        '''
        :property: bool -- Whether this queue has been closed or not.
        '''
        return self._closed

    def close(self):
        '''
        Close this queue and the underlying socket.
        '''
        self._run_sender = False
        self.socket.close()
        self._closed = True

    def empty(self):
        '''
        :returns: bool -- Empty if there is no items to get from this
                          SocketQueue.
        '''
        return self.from_socket_queue.empty()

    def put(self, item):
        '''
        Put item to queue -> codec -> socket.

        :param item: Message object.
                     (Giving ``None`` closes sending - this is to be avoided.)
        :type item: dict, list or None
        '''
        if self._closed or not self._run_sender:
            raise ClosedError('Queue is closed. Cannot send more items.')
        self.to_socket_queue.put(item)

    def get(self):
        '''
        Get message items  <- codec <- socket.

        :returns: Normally a message object (python dict or list) but
                  if socket is closed by peer and queue is drained then
                  ``None`` is returned.
        '''
        if self._drained:
            return None
        obj = self.from_socket_queue.get()
        if obj is None:
            self._drained = True
        return obj

    def _socket_send(self, msg_bytes):
        msglen = len(msg_bytes)
        total = 0
        while total < msglen:
            sent = self.socket.send(msg_bytes[total:])
            if sent == 0:
                # TODO log the error
                self.close()
            total += sent

    def _sender(self):
        while self._run_sender:
            try:
                msg = self.to_socket_queue.get(timeout=0.1)
                msg_bytes = self.codec.into_frame(self.codec.dumps(msg))
                self._socket_send(msg_bytes)
            except Empty:
                pass
            except Exception as e:
                print(e)
                self.close()

    def _receiver(self):
        def _fatal_error(e):
            self.close()
            self._run_receiver = False
            self.from_socket_queue.put(e)
            self.from_socket_queue.put(None)

        bbuffer = b''
        while self._run_receiver:
            try:
                chunk = self.socket.recv(self.BUFSIZE)
                bbuffer += chunk
                b_msg, bbuffer = self.codec.extract_message(bbuffer)
                while b_msg is not None:
                    self.from_socket_queue.put(self.codec.loads(b_msg))
                    b_msg, bbuffer = self.codec.extract_message(bbuffer)
                if chunk == b'':
                    # TODO: just peer closed or error?
                    self._run_receiver = False
                    self.close()
                    self.from_socket_queue.put(None)
            except FramingError as e:
                _fatal_error(e)
            except CodecError as e:
                self.from_socket_queue.put(e)
            except Exception as e:
                _fatal_error(e)
