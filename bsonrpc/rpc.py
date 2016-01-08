# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'

from .framing import JSONFramingRFC7464
from .options import ThreadingModel
from .socket_queue import BSONCodec, JSONCodec, SocketQueue


def _default_id_generator():
    msg_id = 0
    while True:
        msg_id += 1
        yield 'id-%d' % msg_id


class RPCDefaults(object):

    concurrency = ThreadingModel.THREADS
    parallel_request_handling = ThreadingModel.THREADS
    parallel_notification_handling = None

    connection_id = ''
    id_generator = _default_id_generator()


class BSONRpc(RPCDefaults):

    def __init__(self, socket, services=None, **options):
        '''
        :param socket: Socket which is connected to the peer node
        :type socket: socket.socket object
        :param services: Derived class object providing request handlers and
                         notification handlers, used by peer node.
        :type services: RPCServices instance

        TODO: Document options.
        '''
        for key, value in options.items():
            setattr(self, key, value)
        self.services = services
        self.queue = SocketQueue(socket, BSONCodec(), self.concurrency)
        if self.services:
            # TODO: spawn dispatcher.
            pass


class JSONRpc(RPCDefaults):

    #: Default choice for JSON Framing
    framing_cls = JSONFramingRFC7464

    def __init__(self, socket, services=None, **options):
        '''
        :param socket: Socket which is connected to the peer node
        :type socket: socket.socket object
        :param services: Derived class object providing request handlers and
                         notification handlers, used by peer node.
        :type services: RPCServices instance

        TODO: Document options.
        '''
        for key, value in options.items():
            setattr(self, key, value)
        self.services = services
        self.queue = SocketQueue(socket,
                                 JSONCodec(self.framing_cls.extract_message,
                                           self.framing_cls.into_frame),
                                 self.concurrency)
        if self.services:
            # TODO: spawn dispatcher
            pass
