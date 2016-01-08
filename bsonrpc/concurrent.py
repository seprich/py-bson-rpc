# -*- coding: utf-8 -*-
'''
This module provides a collection of concurrency related
object generators. These generators will create either
native threading based or greenlet based objects depending
on which threading_model is selected.
'''

from .options import ThreadingModel


def _spawn_thread(fn, *args, **kwargs):
    from threading import Thread
    t = Thread(target=fn, args=args, kwargs=kwargs)
    t.start()
    return t


def _spawn_greenlet(fn, *args, **kwargs):
    from gevent import Greenlet
    g = Greenlet(fn, *args, **kwargs)
    g.start()
    return g


def spawn(threading_model, fn, *args, **kwargs):
    if threading_model == ThreadingModel.GEVENT:
        return _spawn_greenlet(fn, *args, **kwargs)
    elif threading_model == ThreadingModel.THREADS:
        return _spawn_thread(fn, *args, **kwargs)


def _new_queue(*args, **kwargs):
    from queue import Queue
    return Queue(*args, **kwargs)


def _new_gevent_queue(*args, **kwargs):
    from gevent.queue import Queue
    return Queue(*args, **kwargs)


def new_queue(threading_model, *args, **kwargs):
    if threading_model == ThreadingModel.GEVENT:
        return _new_gevent_queue(*args, **kwargs)
    elif threading_model == ThreadingModel.THREADS:
        return _new_queue(*args, **kwargs)


def _new_thread_lock(*args, **kwargs):
    from threading import Lock
    return Lock(*args, **kwargs)


def _new_gevent_lock(*args, **kwargs):
    from gevent.lock import Semaphore
    return Semaphore(*args, **kwargs)


def new_lock(threading_model, *args, **kwargs):
    if threading_model == ThreadingModel.GEVENT:
        return _new_gevent_lock(*args, **kwargs)
    elif threading_model == ThreadingModel.THREADS:
        return _new_thread_lock(*args, **kwargs)
