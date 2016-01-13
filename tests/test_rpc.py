# -*- coding: utf-8 -*-
import pytest

from bsonrpc.options import ThreadingModel
# from bsonrpc.rpc import BSONRpc, JSONRpc


@pytest.fixture(scope='module',
                params=[ThreadingModel.THREADS, ThreadingModel.GEVENT])
def threading_model(request):
    return request.param


def test_fi(threading_model):
    pass
