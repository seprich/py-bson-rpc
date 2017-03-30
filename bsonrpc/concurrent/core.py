# -*- coding: utf-8 -*-
'''
This module provides a collection of concurrency related
object generators. These generators will create either
native threading based or greenlet based objects depending
on which threading_model is selected.
'''
import six

_gevent_available = False
try:
    from bsonrpc.concurrent.green import *
    _gevent_available = True
except ImportError:
    pass
_asyncio_available = False
if six.PY3:
    try:
        from bsonrpc.concurrent.async import *
        _asyncio_available = True
    except ImportError:
        pass
from bsonrpc.concurrent.util import Promise
from bsonrpc.options import ThreadingModel
from threading import Event, Semaphore, Thread
from six.moves.queue import Queue

__license__ = 'http://mozilla.org/MPL/2.0/'


def _spawn_thread(fn, *args, **kwargs):
    t = Thread(target=fn, args=args, kwargs=kwargs)
    t.start()
    return t


def _with_model(mdict, model):
    try:
        return mdict[model]()
    except Exception as e:
        if model == ThreadingModel.GEVENT and not _gevent_available:
            raise Exception('Attempt to use ThreadingModel.GEVENT without gevent being installed.')
        if model == ThreadingModel.ASYNCIO and not _asyncio_available:
            raise Exception('Attempt to use ThreadingModel.ASYNCIO witout asyncio being installed.')
        raise e


def spawn(threading_model, fn, *args, **kwargs):
    return _with_model({
        # TODO : In asyncio all functions given here must be coroutinized
        ThreadingModel.ASYNCIO: lambda: spawn_coroutine(fn, *args, **kwargs),
        ThreadingModel.GEVENT: lambda: spawn_greenlet(fn, *args, **kwargs),
        ThreadingModel.THREADS: lambda: _spawn_thread(fn, *args, **kwargs),
    }, threading_model)


def new_queue(threading_model, *args, **kwargs):
    return _with_model({
        ThreadingModel.ASYNCIO: lambda: new_asyncio_queue(*args, **kwargs),
        ThreadingModel.GEVENT: lambda: new_gevent_queue(*args, **kwargs),
        ThreadingModel.THREADS: lambda: Queue(*args, **kwargs),
    }, threading_model)


def new_semaphore(threading_model, *args, **kwargs):
    return _with_model({
        ThreadingModel.ASYNCIO: lambda: new_asyncio_semaphore(*args, **kwargs),
        ThreadingModel.GEVENT: lambda: new_gevent_semaphore(*args, **kwargs),
        ThreadingModel.THREADS: lambda: Semaphore(*args, **kwargs),
    }, threading_model)


def new_promise(threading_model):
    return _with_model({
        ThreadingModel.ASYNCIO: lambda: AsyncPromise(new_asyncio_event()),
        ThreadingModel.GEVENT: lambda: Promise(new_gevent_event()),
        ThreadingModel.THREADS: lambda: Promise(Event()),
    }, threading_model)
