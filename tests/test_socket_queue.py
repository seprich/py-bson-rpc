# -*- coding: utf-8 -*-
import pytest

import socket as tsocket
import gevent.socket as gsocket

from bsonrpc.exceptions import DecodingError, EncodingError, FramingError
from bsonrpc.framing import (
    JSONFramingNetstring, JSONFramingNone, JSONFramingRFC7464)
from bsonrpc.options import ThreadingModel
from bsonrpc.socket_queue import BSONCodec, JSONCodec, SocketQueue


msg1 = {
    'jsonrpc': '2.0',
    'id': 'msg-1',
    'method': 'foo',
    'params': [1, 2, 3, 4, 5]
}
msg2 = {
    'jsonrpc': '2.0',
    'id': 'msg-2',
    'method': 'trol',
    'params': {'Good Morning!': 'Selamat Pagi!',
               'How are you?': 'Apa Kabar?'},
}
broken_bytes = b'{"messy": "missy"], ["what": "happens"]}'


@pytest.fixture(scope='module',
                params=[BSONCodec(),
                        JSONCodec(JSONFramingNetstring.extract_message,
                                  JSONFramingNetstring.into_frame),
                        JSONCodec(JSONFramingNone.extract_message,
                                  JSONFramingNone.into_frame),
                        JSONCodec(JSONFramingRFC7464.extract_message,
                                  JSONFramingRFC7464.into_frame)])
def codec(request):
    return request.param


def test_codec(codec):
    partial = codec.into_frame(codec.dumps(msg2))[:20]
    raw_bytes = (codec.into_frame(codec.dumps(msg1)) +
                 codec.into_frame(codec.dumps(msg2)) + partial)
    raw_msg, raw_bytes = codec.extract_message(raw_bytes)
    msg = codec.loads(raw_msg)
    assert msg == msg1
    raw_msg, raw_bytes = codec.extract_message(raw_bytes)
    msg = codec.loads(raw_msg)
    assert msg == msg2
    raw_msg, raw_bytes = codec.extract_message(raw_bytes)
    assert raw_msg is None
    assert raw_bytes == partial


def test_codec_exceptions(codec):
    bb = broken_bytes
    if isinstance(codec, BSONCodec):
        bb = b'\x2c\x00\x00\x00' + broken_bytes
    raw_bytes = (codec.into_frame(bb) +
                 codec.into_frame(codec.dumps(msg1)))
    raw_msg, raw_bytes = codec.extract_message(raw_bytes)
    assert raw_msg is not None
    with pytest.raises(DecodingError):
        codec.loads(raw_msg)
    raw_msg, raw_bytes = codec.extract_message(raw_bytes)
    assert codec.loads(raw_msg) == msg1
    impossible = {'jsonrpc': '2.0', 'id': '99', 'method': test_codec}
    with pytest.raises(EncodingError):
        codec.dumps(impossible)


@pytest.fixture(scope='module',
                params=[ThreadingModel.THREADS, ThreadingModel.GEVENT])
def threading_model(request):
    return request.param


def _socketpair(tmodel):
    if tmodel == ThreadingModel.THREADS:
        return tsocket.socketpair()
    elif tmodel == ThreadingModel.GEVENT:
        return gsocket.socketpair()


def test_socket_queue_basics(codec, threading_model):
    s1, s2 = _socketpair(threading_model)
    sq1 = SocketQueue(s1, codec, threading_model)
    sq2 = SocketQueue(s2, codec, threading_model)
    sq1.put(msg2)
    sq1.put(msg1)
    sq2.put(msg2)
    assert sq2.get() == msg2
    assert sq2.get() == msg1
    assert sq1.get() == msg2
    sq1.close()
    assert sq2.get() is None
    assert sq1.get() is None
    assert sq1.is_closed
    assert sq2.is_closed
    sq1.join()
    sq2.join()


def test_socket_queue_garbage(codec, threading_model):
    s1, s2 = _socketpair(threading_model)
    sq = SocketQueue(s2, codec, threading_model)
    s1.sendall(b'\xfa\xff\xff\xff\xde\xadabracadabra bobby jenkins\x05\x04')
    assert isinstance(sq.get(), FramingError)
    # All but DecodingError's are considered irrecoverable -> socket is closed.
    assert sq.is_closed
    sq.join()
