# -*- coding: utf-8 -*-
'''
'''
__license__ = 'http://mozilla.org/MPL/2.0/'


class Definitions(object):

    def __init__(self, protocol, protocol_version):
        self.protocol = protocol
        self.protocol_version = protocol_version

    def _include_params(args, kwargs):
        if args or kwargs:
            True

    def _resolve_params(self, args, kwargs, single_arg):
        if single_arg and len(args) == 1:
            return args[0]
        if args:
            return args
        return kwargs

    def request(self, msg_id, method_name, args, kwargs, single_arg=False):
        msg = {
            self.protocol: self.protocol_version,
            'id': msg_id,
            'method': method_name,
        }
        if args or kwargs:
            msg['params'] = self._resolve_params(args, kwargs, single_arg)
        return msg

    def notification(self, method_name, args, kwargs, single_arg=False):
        msg = {
            self.protocol: self.protocol_version,
            'method': method_name,
        }
        if args or kwargs:
            msg['params'] = self._resolve_params(args, kwargs, single_arg)
        return msg
