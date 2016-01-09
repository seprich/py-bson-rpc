# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'

from .concurrent import spawn
from .framing import JSONFramingRFC7464
from .options import MessageCodec, ThreadingModel
from .socket_queue import BSONCodec, JSONCodec, SocketQueue


def _default_id_generator():
    msg_id = 0
    while True:
        msg_id += 1
        yield 'id-%d' % msg_id


class RpcBase(object):

    concurrency = ThreadingModel.THREADS
    parallel_request_handling = ThreadingModel.THREADS
    parallel_notification_handling = None

    connection_id = ''
    id_generator = _default_id_generator()

    dispatcher_panic_cb = None

    def __init__(self, socket, codec, services=None, **options):
        for key, value in options.items():
            setattr(self, key, value)
        self.services = services
        self.queue = SocketQueue(socket, codec, self.concurrency)
        if self.services:
            self._dispatcher_thread = spawn(self.concurrency,
                                            self._run_service_dispatcher)
        else:
            self._dispatcher_thread = None

    def invoke_request(self, method_name, *args, **kwargs):
        pass

    def invoke_notification(self, method_name, *args, **kwargs):
        pass

    def get_peer_proxy(self, requests, notifications):
        # lists of strings
        # peer_proxy object.
        pass

    def close(self):
        # stop dispatcher and close
        pass

    def join(self):
        pass

    def _run_service_dispatcher(self):
        pass
        # while True: patch ditch


class BSONRpc(RpcBase):

    def __init__(self, socket, services=None, **options):
        '''
        :param socket: Socket which is connected to the peer node
        :type socket: socket.socket object
        :param services: Derived class object providing request handlers and
                         notification handlers, used by peer node.
        :type services: RPCServices instance

        TODO: Document options.
        '''
        self.codec = MessageCodec.BSON
        super(BSONRpc, self).__init__(socket,
                                      BSONCodec(),
                                      services=services,
                                      **options)


class JSONRpc(RpcBase):

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
        self.codec = MessageCodec.JSON
        framing_cls = options.get('framing_cls', self.framing_cls)
        super(JSONRpc, self).__init__(socket,
                                      JSONCodec(framing_cls.extract_message,
                                                framing_cls.into_frame),
                                      services=services,
                                      **options)

    def batch_call(self, requests, notifications):
        # requests: list of 3-tuples [(<method-name>, args, kwargs,), ...]
        # notifications: list of 3-tuples
        # returns list of result tuples / Exception objects
        # raises error only if parse error from peer...
        return None  # create batch object
