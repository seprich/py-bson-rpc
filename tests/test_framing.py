# -*- coding: utf-8 -*-
import pytest

from bsonrpc.exceptions import FramingError
from bsonrpc.framing import (
    JSONFramingNetstring, JSONFramingNone, JSONFramingRFC7464)


valid_msg1 = (b'{"id":"2","jsonrpc":"2.0","method":"sum",'
              b'"params":{"a":3,"b":4,"c":false}}')

valid_msg2 = (b'{"id":"43","jsonrpc":"3.0","method":"toast","params":{'
              b'"first":"tadaa","second":"tr\\u00e4d\\u00e4\\u00e4"}}')

valid_msg3 = (b'{"id":"msg-1","jsonrpc":"2.0","method":"foo",'
              b'"params":[1,2,3,4,5]}')

part_1 = b'{"id":"12","jsonrpc":"2.0","method":"s'
part_2 = b'umer","params":{"a":2,"b":1,"c":false}}'


def test_frameless_extract():
    raw_bytes = valid_msg1 + valid_msg2 + part_1 + part_2 + part_1
    msg, rest = JSONFramingNone.extract_message(raw_bytes)
    assert msg == valid_msg1
    msg, rest = JSONFramingNone.extract_message(rest)
    assert msg == valid_msg2
    msg, rest = JSONFramingNone.extract_message(rest)
    assert msg == (part_1 + part_2)
    msg, rest = JSONFramingNone.extract_message(rest)
    assert msg is None
    assert rest == part_1


def test_frameless_extract2():
    msg, rest = JSONFramingNone.extract_message(valid_msg3)
    assert msg == valid_msg3
    assert rest == b''


def test_frameless_extract_broken():
    raw_bytes = valid_msg1 + b'  invalid con}ent'
    msg, raw_bytes = JSONFramingNone.extract_message(raw_bytes)
    assert msg == valid_msg1
    with pytest.raises(FramingError):
        JSONFramingNone.extract_message(raw_bytes)


def test_frameless_frame():
    assert JSONFramingNone.into_frame(valid_msg2) == valid_msg2


def test_rfc_7464_extract():
    raw_bytes = (b'\x1e' + valid_msg1 + b'\n\x1e' + valid_msg2 +
                 b'\n\x1e' + part_1)
    msg, raw_bytes = JSONFramingRFC7464.extract_message(raw_bytes)
    assert msg == valid_msg1
    msg, raw_bytes = JSONFramingRFC7464.extract_message(raw_bytes)
    assert msg == valid_msg2
    msg, raw_bytes = JSONFramingRFC7464.extract_message(raw_bytes)
    assert msg is None
    assert raw_bytes == b'\x1e' + part_1


def test_rfc_7464_extract_broken():
    raw_bytes = b'\x1e' + valid_msg1 + b'\n' + valid_msg2 + b'\n'
    msg, raw_bytes = JSONFramingRFC7464.extract_message(raw_bytes)
    assert msg == valid_msg1
    with pytest.raises(FramingError):
        JSONFramingRFC7464.extract_message(raw_bytes)


def test_netstring_extract():
    raw_bytes = b'74:' + valid_msg1 + b',104:' + valid_msg2 + b',77:' + part_1
    msg, raw_bytes = JSONFramingNetstring.extract_message(raw_bytes)
    assert msg == valid_msg1
    msg, raw_bytes = JSONFramingNetstring.extract_message(raw_bytes)
    assert msg == valid_msg2
    msg, raw_bytes = JSONFramingNetstring.extract_message(raw_bytes)
    assert msg is None
    assert raw_bytes == b'77:' + part_1


def test_netstring_extract_broken():
    raw_bytes = b'104:' + valid_msg2 + b',23:' + valid_msg1
    msg, raw_bytes = JSONFramingNetstring.extract_message(raw_bytes)
    assert msg == valid_msg2
    with pytest.raises(FramingError):
        JSONFramingNetstring.extract_message(raw_bytes)


def test_netstring_frame():
    framed = JSONFramingNetstring.into_frame(valid_msg2)
    assert framed == b'104:' + valid_msg2 + b','
