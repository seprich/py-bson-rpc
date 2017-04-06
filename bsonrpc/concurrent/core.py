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
from bsonrpc.concurrent.util import Promise, Either
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

    
class Tasking(object):
    
    def __init__(self, threading_model, quotas={}):
        self._model = threading_model
        self._quotas = {
            k: new_semaphore(threading_model, v)
            for k, v in quotas.items()
            if isinstance(v, six.integer_types) and v >= 0
        }
        self._lock = new_semaphore(threading_model)
        self._active_threads = []
        
    def _add_thread(self, thr):
        def _is_alive(thr):
            return ((self._model == ThreadingModel.GEVENT and not thr.ready()) or
                    (self._model == ThreadingModel.THREADS and thr.is_alive()))

        with self._lock:
            # Cleanup
            self._active_threads = list(filter(lambda t: _is_alive(t), self._active_threads))
            # Add
            self._active_threads.append(thr)

    def _routine(self, group, promise, fn, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
            promise.set(Either.Left(result))
        except Exception as e:
            promise.set(Either.Right(e))
        if group in self._quotas:
            self._quotas[group].release()
        
    def spawn_task(self, group, fn, *args, **kwargs):
        if group in self._quotas:
            # yield from
            self._quotas[group].acquire()
        promise = new_promise(self._model)
        thr = spawn(self._model, self._routine, group, promise, fn, *args, **kwargs)
        self._add_thread(thr)
        return promise
        
    def join(self, timeout=None):
        def _totaljoiner():
            with self._lock:
                for thr in self._active_threads:
                    thr.join()
        joiner_thread = spawn(self._model, _totaljoiner)
        joiner_thread.join(timeout)