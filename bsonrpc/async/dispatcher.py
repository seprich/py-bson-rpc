# -*- coding: utf-8 -*-
'''
'''
import asyncio

from bsonrpc.dispatcher import Dispatcher

__license__ = 'http://mozilla.org/MPL/2.0/'


class AsyncDispatcher(Dispatcher):
    
    @asyncio.coroutine
    def run(self):
        self._log_info(u'Start RPC message dispatcher.')
        while True:
            try:
                msg = yield from self.rpc.socket_queue.get()
                if msg is None:
                    break
                self._log_info(u'Dispatch message.')
                if isinstance(msg, Exception):
                    # NOTE No need to run as coroutine
                    self._handle_parse_error(msg)
                else:
                    # NOTE Spawn coroutines in handlers
                    self._resolve_message_handler(msg)(msg)
            except Exception as e:
                self._log_error(e)
        self._log_info(u'Exit RPC message dispatcher.')
        
    @asyncio.coroutine
    def join(self, timeout=None):
        all_tasks = [self._thread] + self._active_threads
        yield from asyncio.wait(all_tasks, timeout=timeout)