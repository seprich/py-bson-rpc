# -*- coding: utf-8 -*-
import os
import pytest
import six

tmodel = os.environ['TT']

if tmodel == 'threads':
    import socket
if tmodel == 'gevent': 
    import gevent.socket as socket

from bsonrpc.exceptions import InvalidParams, ServerError
from bsonrpc.interfaces import (
    notification, request, rpc_request, service_class)
from bsonrpc.options import ThreadingModel
from bsonrpc.rpc import BSONRpc, JSONRpc
from bsonrpc.util import BatchBuilder


def _socketpair(tmodel):
    return socket.socketpair()


@pytest.fixture(scope='module',
                params=[BSONRpc, JSONRpc])
def protocol_cls(request):
    return request.param


if tmodel == 'threads':
    option_combinations = [
        (ThreadingModel.THREADS, ThreadingModel.THREADS, ThreadingModel.THREADS),
    ]
elif tmodel == 'gevent':
    option_combinations = [
        (ThreadingModel.GEVENT, ThreadingModel.GEVENT, ThreadingModel.GEVENT),
    ]
else:
    option_combinations = []


@pytest.fixture(scope='module',
                params=option_combinations)
def options(request):
    return {
        'threading_model': request.param[0],
        'concurrent_request_handling': request.param[1],
        'concurrent_notification_handling': request.param[2],
    }


@service_class
class ServerServices(object):

    def __init__(self):
        self.history = []

    @request
    def swapper(self, txt):
        self.history.append(('swapper', txt))
        return ''.join(reversed(list(txt)))

    @rpc_request
    def complicated(self, rpc, a, b, c):
        self.history.append(('complicated', a, b, c))
        # Notification to peer
        rpc.invoke_notification('report_back', 'Hello', 'There')
        # Send Notification using peer proxy
        client = rpc.get_peer_proxy([], ['report_back'])
        client.report_back('Other Way')
        return (u'a: %s b: %s c: %s' %
                (six.text_type(a), six.text_type(b), six.text_type(c)))

    @rpc_request
    def server_disconnect(self, rpc, a, b):
        self.history.append(('server_disconnect', a, b))
        rpc.close_after_response()
        return a * b

    @notification
    def yaman(self, neva_sei_neva):
        self.history.append(('yaman', neva_sei_neva))

    @request
    def intensive(self, rank):
        self.history.append(('intensive', rank))
        value = 0.0
        for k in range(1, 2 * rank + 1, 2):
            sign = -(k % 4 - 2)
            value += float(sign) / k
        return 4 * value

    @request
    def panicker(self, txt):
        self.history.append(('panicker', txt))
        if txt == 'Sister Sledge':
            raise Exception('We are Family!')
        if txt == 'Tina Turner':
            raise Exception('Proud Mary!')
        raise Exception('Thriller!')


@service_class
class ClientServices(object):

    def __init__(self):
        self.history = []

    @notification
    def report_back(self, txt, opt=123):
        self.history.append(('report_back', txt, opt))


def test_simple_request(protocol_cls, options):
    s1, s2 = _socketpair(options['threading_model'])
    services = ServerServices()
    srv = protocol_cls(s1, services, **options)
    cli = protocol_cls(s2, **options)
    proxy = cli.get_peer_proxy(['swapper'], [])
    result = proxy.swapper('Hello There!')
    assert result == '!erehT olleH'
    cli.close()
    srv.join()
    assert services.history == [('swapper', 'Hello There!')]


def _basix(p_cls, opt):
    s1, s2 = _socketpair(opt['threading_model'])
    srv_ser = ServerServices()
    cli_ser = ClientServices()
    srv = p_cls(s1, srv_ser, **opt)
    cli = p_cls(s2, cli_ser, **opt)
    return srv_ser, cli_ser, srv, cli


def test_complicated_request(protocol_cls, options):
    srv_ser, cli_ser, srv, cli = _basix(protocol_cls, options)
    proxy = cli.get_peer_proxy()
    result = proxy.complicated(u'First', u'Second', u'Third')
    assert result == u'a: First b: Second c: Third'
    cli.close()
    srv.join()
    cli.join()
    assert srv_ser.history == [('complicated', 'First', 'Second', 'Third')]
    assert cli_ser.history == [('report_back', 'Hello', 'There'),
                               ('report_back', 'Other Way', 123)]


def test_server_disconnect(protocol_cls, options):
    srv_ser, cli_ser, srv, cli = _basix(protocol_cls, options)
    proxy = cli.get_peer_proxy()
    result = proxy.server_disconnect(12, 34)
    assert result == 408
    srv.join(timeout=1.0)
    cli.join(timeout=1.0)
    assert srv.is_closed
    assert cli.is_closed
    assert srv_ser.history == [('server_disconnect', 12, 34)]


def test_batch(options):
    srv_ser, cli_ser, srv, cli = _basix(JSONRpc, options)
    b1 = BatchBuilder(['complicated', 'swapper'], ['yaman'])
    b1.yaman('note')
    b1.swapper('firstie')
    b1.complicated('q!', 'w!', 'e!')
    b1.yaman('again')
    b1.swapper('thirstie')
    results = cli.batch_call(b1)
    assert results == ['eitsrif', 'a: q! b: w! c: e!', 'eitsriht']
    b2 = BatchBuilder()
    b2.n.yaman('Noting but')
    b2.n.yaman('notifications only')
    results = cli.batch_call(b2)
    assert results is None
    b3 = BatchBuilder()
    b3.server_disconnect(3, 4)
    b3.swapper('gaga', 'trolo')
    b3.swapper()
    b3.swapper('SomethinG')
    results = cli.batch_call(b3)
    assert len(results) == 4
    assert results[0] == 12
    assert isinstance(results[1], InvalidParams)
    assert isinstance(results[2], InvalidParams)
    assert results[3] == 'GnihtemoS'
    srv.join(1.0)
    cli.join(1.0)
    assert srv.is_closed
    assert cli.is_closed


def test_exception(protocol_cls, options):
    srv_ser, cli_ser, srv, cli = _basix(protocol_cls, options)
    proxy = cli.get_peer_proxy()
    with pytest.raises(ServerError):
        proxy.panicker('Tina Turner')
    with pytest.raises(ServerError):
        proxy.panicker('Michael Jackson')
    cli.close()
