# -*- coding: utf-8 -*-
'''
Library for JSON RPC 2.0 and BSON RPC
'''
import six

from bsonrpc.exceptions import BsonRpcError
from bsonrpc.framing import (
    JSONFramingNetstring, JSONFramingNone, JSONFramingRFC7464)
from bsonrpc.interfaces import (
    notification, request, rpc_notification, rpc_request, service_class)
from bsonrpc.options import NoArgumentsPresentation, ThreadingModel
from bsonrpc.rpc import BSONRpc, JSONRpc
from bsonrpc.util import BatchBuilder
_asyncio_available = False
if six.PY3:
    try:
        from bsonrpc.protocol import BSONRPCProtocolFactory, JSONRPCProtocolFactory
        _asyncio_available = True
    except ImportError:
        pass


__version__ = '0.2.0'

__license__ = 'http://mozilla.org/MPL/2.0/'

__all__ = [
    'BSONRpc',
    'BatchBuilder',
    'BsonRpcError',
    'JSONFramingNetstring',
    'JSONFramingNone',
    'JSONFramingRFC7464',
    'JSONRpc',
    'NoArgumentsPresentation',
    'ThreadingModel',
    'notification',
    'request',
    'rpc_notification',
    'rpc_request',
    'service_class',
]
if _asyncio_available:
    __all__.extend([
        'BSONRPCProtocolFactory',
        'JSONRPCProtocolFactory',
    ])
