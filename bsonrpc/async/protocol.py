# -*- coding: utf-8 -*-
'''
'''
import asyncio
    
from asyncio import Queue
from bsonrpc.async.socket_queue import ProtocolQueue
from bsonrpc.exceptions import BsonRpcError, DecodingError
from bsonrpc.framing import JSONFramingRFC7464
from bsonrpc.options import MessageCodec
from bsonrpc.rpc import RpcBase
from bsonrpc.socket_queue import BSONCodec, JSONCodec

__license__ = 'http://mozilla.org/MPL/2.0/'


class Reference(object):

    def __init__(self, ref):
        self._ref = ref

    def _set(self, ref):
        self._ref = ref

    def __getattr__(self, name):
        return getattr(self._ref, name)

    def __bool__(self):
        return (self._ref is not None)


class TransportInfo(object):

    def __init__(self):
        self.transport_info = {}

    def _collect_transport_info(self, transport):
        keys = ['peername', 'socket', 'sockname', 'compression',
                'cipher', 'peercert', 'sslcontext', 'ssl_object',
                'pipe', 'subprocess']
        for key in keys:
            self.transport_info[key] = transport.get_extra_info(key, None)


class BSONRPCProtocol(RpcBase, TransportInfo, asyncio.Protocol):

    protocol = 'bsonrpc'
    protocol_version = '2.0'

    def __init__(self, loop, services, with_connection, **options):
        self.codec = MessageCodec.BSON
        for key, value in options.items():
            setattr(self, key, value)
        self.loop = loop
        if not services:
            services = DefaultServices()
        self._with_connection = with_connection
        bson_codec = BSONCodec(
            custom_codec_implementation=self.custom_codec_implementation)
        self._transport = Reference(None)
        self._protocol_queue = ProtocolQueue(self._transport, bson_codec)
        RpcBase.__init__(self, self._protocol_queue, services, **options)
        TransportInfo.__init__(self)
        asyncio.Protocol.__init__(self)

    def connection_made(self, transport):
        self._collect_transport_info(transport)
        self._transport._set(transport)
        if self.loop and callable(self._with_connection):
            self.loop.call_soon(self._with_connection, self)

    def connection_lost(self, exc):
        self._protocol_queue.connection_lost(exc)

    def data_received(self, data):
        self._protocol_queue.data_received(data)


class JSONRPCProtocol(RpcBase, TransportInfo, asyncio.Protocol):

    protocol = 'jsonrpc'
    protocol_version = '2.0'
    framing_cls = JSONFramingRFC7464

    def __init__(self, loop, services, with_connection, **options):
        self.codec = MessageCodec.JSON
        for key, value in options.items():
            setattr(self, key, value)
        self.loop = loop
        if not services:
            services = DefaultServices()
        self._with_connection = with_connection
        json_codec = JSONCodec(
            self.framing_cls.extract_message,
            self.framing_cls.into_frame,
            custom_codec_implementation=self.custom_codec_implementation)
        self._transport = Reference(None)
        self._protocol_queue = ProtocolQueue(self._transport, json_codec)
        RpcBase.__init__(self, self._protocol_queue, services, **options)
        TransportInfo.__init__(self)
        asyncio.Protocol.__init__(self)

    def connection_made(self, transport):
        self._collect_transport_info(transport)
        self._transport._set(transport)
        if self.loop and callable(self._with_connection):
            self.loop.call_soon(self._with_connection, self)

    def connection_lost(self, exc):
        self._protocol_queue.connection_lost(exc)

    def data_received(self, data):
        self._protocol_queue.data_received(data)


class _Factory(object):

    def __init__(self, cls, loop, services_factory, with_connection, **options):
        self._cls = cls
        self._loop = loop
        self._services_factory = services_factory
        self._with_connection = with_connection
        self._options = options

    def __call__(self):
        services = None
        if callable(self._services_factory):
            services = self._services_factory()
        elif hasattr(self._services_factory, 'create'):
            services = self._services_factory.create()
        return self._cls(self._loop, services, with_connection, **self._options)

    def create(self):
        return self.__call__()


class BSONRPCProtocolFactory(_Factory):

    def __init__(self, loop=None, services_factory=None, with_connection=None, **options):
        super(BSONRPCProtocolFactory, self).__init__(BSONRPCProtocol, loop, services_factory, with_connection, **options)


class JSONRPCProtocolFactory(_Factory):

    def __init__(self, loop=None, services_factory=None, with_connection=None, **options):
        super(JSONRPCProtocolFactory, self).__init__(JSONRPCProtocol, loop, services_factory, with_connection, **options)
