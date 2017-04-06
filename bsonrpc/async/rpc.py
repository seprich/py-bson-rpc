# -*- coding: utf-8 -*-
'''
'''

from bsonrpc.async import AsyncDispatcher
from bsonrpc.rpc import RpcBase

__license__ = 'http://mozilla.org/MPL/2.0/'


class AsyncRpcBase(RpcBase):
    
    def _new_dispatcher(self):
        return AsyncDispatcher(self)
    
    
    