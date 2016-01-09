# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'


class PeerProxy(object):

    def __init__(self, rpc, requests, notifications):
        self._rpc = rpc
        self._requests = requests
        self._notifications = notifications

    def __getattr__(self, name):
        if name in self._requests:
            def _curried(*args, **kwargs):
                return self._rpc.invoke_request(name, *args, **kwargs)
            return _curried
        elif name in self._notifications:
            def _curried(*args, **kwargs):
                return self._rpc.invoke_notification(name, *args, **kwargs)
            return _curried
        raise AttributeError(
            "'%s' object has no attribute '%s'" %
            (self.__class__.__name__, name))
