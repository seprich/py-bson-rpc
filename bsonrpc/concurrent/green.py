# -*- coding: utf-8 -*-
'''
'''
from gevent import Greenlet
from gevent.event import Event
from gevent.lock import Semaphore
from gevent.queue import Queue

__license__ = 'http://mozilla.org/MPL/2.0/'


def spawn_greenlet(fn, *args, **kwargs):
    g = Greenlet(fn, *args, **kwargs)
    g.start()
    return g


def new_gevent_queue(*args, **kwargs):
    return Queue(*args, **kwargs)


def new_gevent_semaphore(*args, **kwargs):
    return Semaphore(*args, **kwargs)


def new_gevent_event():
    return Event()
