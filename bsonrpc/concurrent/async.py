# -*- coding: utf-8 -*-
'''
'''
import asyncio

from bsonrpc.concurrent.util import Promise

__license__ = 'http://mozilla.org/MPL/2.0/'


class AsyncPromise(Promise):

    @asyncio.coroutine
    def wait(self, timeout=None):
        yield from asyncio.wait([self._event.wait()], timeout=timeout)
        if not self._event.is_set():
            raise RuntimeError(
                u'Promise timeout after %.02f seconds.' % timeout)
        return self._value


@asyncio.coroutine
def _ensure_coroutine(fn, *args, **kwargs):
    return fn(*args, **kwargs)


def spawn_coroutine(fn, *args, **kwargs):
    return asyncio.ensure_future(_ensure_coroutine(fn, *args, **kwargs))


def new_asyncio_semaphore(*args, **kwargs):
    return asyncio.Semaphore(*args, **kwargs)


def new_asyncio_event():
    return asyncio.Event()


def new_asyncio_queue(*args, **kwargs):
    return asyncio.Queue(*args, **kwargs)
