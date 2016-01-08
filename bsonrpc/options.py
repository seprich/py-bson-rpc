# -*- coding: utf-8 -*-
'''
Library wide option keys.
'''
__license__ = 'http://mozilla.org/MPL/2.0/'


class MessageCodec(object):

    BSON = 'bson'

    JSON = 'json'


class ThreadingModel(object):

    THREADS = 'threads'

    GEVENT = 'gevent'
