# -*- coding: utf-8 -*-
'''
Library for JSON RPC 2.0 and BSON RPC

Install with pip3

And use:
    ``import bsonrpc``
'''
__license__ = 'http://mozilla.org/MPL/2.0/'

from .rpc import BSONRpc, JSONRpc


__all__ = [
    'BSONRpc',
    'JSONRpc',
]
