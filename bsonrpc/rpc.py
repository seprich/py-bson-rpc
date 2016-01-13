# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'

from .concurrent import new_queue, spawn
from .definitions import Definitions
#from .exceptions import CodecError
from .framing import JSONFramingRFC7464
from .interfaces import PeerProxy
from .options import MessageCodec, ThreadingModel
from .socket_queue import BSONCodec, JSONCodec, SocketQueue


def _default_id_generator():
    msg_id = 0
    while True:
        msg_id += 1
        yield msg_id


class Dispatcher(object):

    def __init__(self, threading_model, queue):
        self._threading_model = threading_model
        self._queue = queue
        self._thread = spawn(threading_model, self.run)
        self._responses = {}

    def register(self, msg_id):
        queue = new_queue(self._threading_model)
        self._responses[msg_id] = queue
        return queue

    def unregister(self, msg_id):
        del self._responses[msg_id]

    def run(self):
        while True:
            try:
                msg = self._queue.get()
            except Exception as e:
                pass

    def join(self):
        self._thread.join()


class RpcBase(object):

    threading_model = ThreadingModel.THREADS
    parallel_request_handling = ThreadingModel.THREADS
    parallel_notification_handling = None

    connection_id = ''
    id_generator = _default_id_generator()

    dispatcher_panic_cb = None

    def __init__(self, socket, codec, services=None, **options):
        for key, value in options.items():
            setattr(self, key, value)
        self._def = Definitions(self.protocol, self.protocol_version)
        self.services = services
        self.queue = SocketQueue(socket, codec, self.threading_model)
        self.dispatcher = Dispatcher(self.threading_model, self.queue)

    def invoke_request(self, method_name, *args, **kwargs):
        def _send_request(msg_id):
            try:
                result_queue = self.dispatcher.register(msg_id)
                self.queue.put(
                    self._def.request(msg_id, method_name, args, kwargs))
                return result_queue
            except Exception as e:
                self.dispatcher.unregister(msg_id)
                raise e

        msg_id = next(self.id_generator)
        queue = _send_request(msg_id)
        result = queue.get()
        if isinstance(result, Exception):
            raise result
        return result

    def invoke_notification(self, method_name, *args, **kwargs):
        self.queue.put(
            self._def.notification(method_name, args, kwargs))

    def get_peer_proxy(self, requests, notifications):
        return PeerProxy(self, requests, notifications)

    def close(self):
        # stop dispatcher and close
        pass

    def join(self):
        pass


class BSONRpc(RpcBase):

    protocol = 'bsonrpc'
    protocol_version = '2.0'

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

    protocol = 'jsonrpc'
    protocol_version = '2.0'

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
