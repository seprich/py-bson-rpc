# -*- coding: utf-8 -*-
import pytest

from bsonrpc.exceptions import DecodingError, EncodingError
from bsonrpc.framing import (
    JSONFramingNetstring, JSONFramingNone, JSONFramingRFC7464)
from bsonrpc.socket_queue import BSONCodec, JSONCodec


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
    # bson dumps just silently omits non-encodable entities...
    # -> https://github.com/py-bson/bson/issues/36
    if not isinstance(codec, BSONCodec):
        impossible = {'jsonrpc': '2.0', 'id': '99', 'method': test_codec}
        with pytest.raises(EncodingError):
            codec.dumps(impossible)


# TODO: Test the SocketQueue
