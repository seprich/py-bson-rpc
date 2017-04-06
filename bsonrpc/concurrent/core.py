# -*- coding: utf-8 -*-
'''
This module provides a collection of concurrency related
object generators. These generators will create either
native threading based or greenlet based objects depending
on which threading_model is selected.
'''
import six
import sys

try:
    from bsonrpc.concurrent import green
except ImportError:
    green = None
if six.PY3:
    try:
        from bsonrpc.concurrent import async as alib
    except ImportError:
        alib = None
else:
    alib = None
from bsonrpc.concurrent.util import Promise
from bsonrpc.options import ThreadingModel
from threading import Event, Semaphore, Thread
from six.moves.queue import Queue

__license__ = 'http://mozilla.org/MPL/2.0/'


def _sanity(tmodel):
    if tmodel == ThreadingModel.ASYNCIO and alib is None:
        raise Exception('Attempt to use ThreadingModel.ASYNCIO without asyncio being installed.')
    if tmodel == ThreadingModel.GEVENT and green is None:
        raise Exception('Attempt to use ThreadingModel.GEVENT without gevent being installed.')


def _spawn_thread(fn, *args, **kwargs):
    t = Thread(target=fn, args=args, kwargs=kwargs)
    t.start()
    return t


def spawn(threading_model, fn, *args, **kwargs):
    try:
        if threading_model == ThreadingModel.ASYNCIO:
            return alib.spawn_coroutine(fn, *args, **kwargs)
        elif threading_model == ThreadingModel.GEVENT:
            return green.spawn_greenlet(fn, *args, **kwargs)
        elif threading_model == ThreadingModel.THREADS:
            return _spawn_thread(fn, *args, **kwargs)
    except AttributeError as e:
        _sanity(threading_model)
        raise e


def new_queue(threading_model, *args, **kwargs):
    try:
        if threading_model == ThreadingModel.ASYNCIO:
            return alib.new_asyncio_queue(*args, **kwargs)
        elif threading_model == ThreadingModel.GEVENT:
            return green.new_gevent_queue(*args, **kwargs)
        elif threading_model == ThreadingModel.THREADS:
            return Queue(*args, **kwargs)
    except AttributeError as e:
        _sanity(threading_model)
        raise e


def new_semaphore(threading_model, *args, **kwargs):
    try:
        if threading_model == ThreadingModel.ASYNCIO:
            return alib.new_asyncio_semaphore(*args, **kwargs)
        elif threading_model == ThreadingModel.GEVENT:
            return green.new_gevent_semaphore(*args, **kwargs)
        elif threading_model == ThreadingModel.THREADS:
            return Semaphore(*args, **kwargs)
    except AttributeError as e:
        _sanity(threading_model)
        raise e


def new_promise(threading_model):
    try:
        if threading_model == ThreadingModel.ASYNCIO:
            return alib.AsyncPromise(alib.new_asyncio_event())
        elif threading_model == ThreadingModel.GEVENT:
            return Promise(green.new_gevent_event())
        elif threading_model == ThreadingModel.THREADS:
            return Promise(Event())
    except AttributeError as e:
        _sanity(threading_model)
        raise e


class Tasker(object):
    
    def __init__(self, threading_model, quotas={}):
        self._model = threading_model
        self._lock = new_semaphore(threading_model)
        self._quotas = {
            k: new_semaphore(threading_model, v)
            for k, v in quotas.items() if isinstance(v, six.integer_types)
        }
        self._idx = 0
        
    def _next_index(self):
        with self._lock:
            self._idx = (self._idx + 1) % sys.maxsize
            return self._idx
        
    
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    