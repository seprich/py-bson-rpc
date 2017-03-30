# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'


class Promise(object):

    def __init__(self, event):
        object.__setattr__(self, '_event', event)
        object.__setattr__(self, '_value', None)

    def __getattr__(self, name):
        return getattr(self._event, name)

    def __setattr__(self, name, value):
        if hasattr(self._event, name):
            object.__setattr__(self._event, name, value)
        else:
            object.__setattr__(self, name, value)

    @property
    def value(self):
        return self._value

    def set(self, value):
        object.__setattr__(self, '_value', value)
        self._event.set()

    def wait(self, timeout=None):
        if not self._event.wait(timeout):
            raise RuntimeError(
                u'Promise timeout after %.02f seconds.' % timeout)
        return self._value