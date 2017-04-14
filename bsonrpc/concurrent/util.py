# -*- coding: utf-8 -*-
'''
'''

import six

__license__ = 'http://mozilla.org/MPL/2.0/'


@six.python_2_unicode_compatible
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
    
    def __str__(self):
        if self.is_set():
            return u'%s(is_set: True, value: %s)' % (self.__class__.__name__, six.text_type(self.value))
        return u'%s(is_set: False)' % self.__class__.__name__


@six.python_2_unicode_compatible
class Either(object):
    
    @staticmethod
    def Left(value):
        return Left(value)
    
    @staticmethod
    def Right(value):
        return Right(value)
    
    def is_left(self):
        return isinstance(self, Left)
    
    def is_right(self):
        return isinstance(self, Right)
    
    def __str__(self):
        return u'%s(value: %s)' % (self.__class__.__name__, six.text_type(self._value))


class Left(Either):
        
    def __init__(self, value):
        self._value = value
        
    @property
    def left(self):
        return self._value


class Right(Either):
        
    def __init__(self, value):
        self._value = value
        
    @property
    def right(self):
        return self._value