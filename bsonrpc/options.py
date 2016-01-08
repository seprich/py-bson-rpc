# -*- coding: utf-8 -*-
'''
Library wide option keys.
'''


class MessageCodec(object):

    BSON = 'bson'

    JSON = 'json'


class ThreadingModel(object):

    THREADS = 'threads'

    GEVENT = 'gevent'
