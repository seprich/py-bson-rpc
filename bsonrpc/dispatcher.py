# -*- coding: utf-8 -*-
'''
Dispatcher for RPC Objects. Routes messages and executes services.
'''
import logging
import six

from bsonrpc.concurrent import new_promise, spawn
from bsonrpc.concurrent import Tasking
from bsonrpc.definitions import RpcErrors
from bsonrpc.exceptions import BsonRpcError
from bsonrpc.options import ThreadingModel

__license__ = 'http://mozilla.org/MPL/2.0/'


class RpcForServices(object):

    def __init__(self, rpc):
        self._rpc = rpc
        self._close_after = False
        self._aborted = False

    @property
    def aborted(self):
        return self._aborted

    @property
    def close_after_response_requested(self):
        return self._close_after

    def __getattr__(self, name):
        if name in ('close', 'join',) or name.startswith('_'):
            raise AttributeError(
                "'%s' is not allowed within service handler.'" % name)
        return getattr(self._rpc, name)

    def abort(self):
        self._aborted = True
        self._rpc.close()

    def close_after_response(self):
        self._close_after = True


class Dispatcher(object):
    
    gid_dispatcher = 'dispatcher'
    gid_handlers = 'handlers'
    gid_batches = 'batches'

    def __init__(self, rpc):
        '''
        :param rpc: Rpc parent object.
        :type rpc: RpcBase
        '''
        self.rpc = rpc
        # {"<msg_id>": <promise>, ...}
        self._responses = {}
        # { ("<msg_id>", "<msg_id>",): promise, ...}
        self._batch_responses = {}
        self.conn_label = six.text_type(
            self.rpc.connection_id and '%s: ' % self.rpc.connection_id)
        self._tasking = Tasking(self.rpc.threading_model)
        
    def start(self):
        self._tasking.spawn_task(self.gid_dispatcher, self.run)

    def __getattr__(self, name):
        return getattr(self.rpc, name)

    def _log_info(self, msg, *args, **kwargs):
        logging.info(self.conn_label + six.text_type(msg), *args, **kwargs)

    def _log_error(self, msg, *args, **kwargs):
        logging.error(self.conn_label + six.text_type(msg), *args, **kwargs)

    def register_expect_response(self, msg_id):
        promise = new_promise(self.rpc.threading_model)
        self._responses[msg_id] = promise
        return promise
    
    def deregister_expect_response(self, msg_id):
        if msg_id in self._responses:
            promise = self._responses[msg_id]
            del self._responses[msg_id]
            if not promise.is_set():
                promise.set(BsonRpcError(u'Timeout'))
                
    def register_expect_batch_response(self, msg_ids_tuple):
        promise = new_promise(self.rpc.threading_model)
        self._batch_responses[msg_ids_tuple] = promise
        return promise
            
    def deregister_expect_batch_response(self, msg_ids_tuple):
        if msg_ids_tuple in self._batch_responses:
            promise = self._batch_responses[msg_ids_tuple]
            del self._batch_responses[msg_ids_tuple]
            if not promise.is_set():
                promise.set(BsonRpcError(u'Timeout'))
    
    def _get_params(self, msg):
        if 'params' not in msg:
            return [], {}
        params = msg['params']
        if isinstance(params, list):
            return params, {}
        if isinstance(params, dict):
            return [], params
        
    def _is_compatible(self, method, args, kwargs):
        spec = method._argspec
        possible_args = (spec.args[2:] if method._with_rpc else  spec.args[1:])
        required_args = possible_args[-(len(spec.defaults) if spec.defaults else 0):]
        if len(args):
            return (len(args) >= len(required_args) and
                    (len(args) <= len(possible_args) or spec.varargs))
        elif len(kwargs):
            all_present = set(kwargs.keys())
            if not set(required_args).issubset(all_present):
                return False
            extras_present = all_present.difference(set(possible_args))
            return (spec.keywords is not None or not extras_present)
        else:
            return (len(required_args) == 0)
        
    def _post_processing(self, rfs):
        if rfs.aborted:
            self._log_info(u'Connection aborted in request handler.')
        elif rfs.close_after_response_requested:
            self.rpc.close()
            self._log_info(
                u'RPC closed due to invocation by Request/Notification handler.')

    def _execute_request(self, msg, rfs):
        msg_id = msg['id']
        method_name = msg['method']
        args, kwargs = self._get_params(msg)
        try:
            method = self.rpc.services._request_handlers.get(method_name)
            if method:
                if not self._is_compatible(method, args, kwargs):
                    return self.rpc.definitions.error_response(
                        msg_id, RpcErrors.invalid_params)
                result = method(self.rpc.services, rfs, *args, **kwargs)
                return self.rpc.definitions.ok_response(msg_id, result)
            else:
                return self.rpc.definitions.error_response(
                    msg_id, RpcErrors.method_not_found)
        except Exception as e:
            return self.rpc.definitions.error_response(
                msg_id, RpcErrors.server_error, six.text_type(e))

    def _handle_request(self, msg, rfs=None):
        self._log_info(u'Handle request: ' + six.text_type(msg))
        within_batch = (rfs is not None)
        if not rfs:
            rfs = RpcForServices(self.rpc)
        response = self._execute_request(msg, rfs)
        if not within_batch:
            if not rfs.aborted:
                self.rpc.socket_queue.put(response)
                self._log_info(u'Sent response: ' + six.text_type(response))
            self._post_processing(rfs)
        return response

    def _handle_notification(self, msg, rfs=None):
        self._log_info(u'Handle notification: ' + six.text_type(msg))
        within_batch = (rfs is not None)
        if not rfs:
            rfs = RpcForServices(self.rpc)
        method_name = msg['method']
        args, kwargs = self._get_params(msg)
        try:
            method = self.rpc.services._notification_handlers.get(method_name)
            if method:
                if not self._is_compatible(method, args, kwargs):
                    self._log_error(
                        u'Notification method %s called with incompatible '
                        u'arguments: %s %s' % 
                        (method_name, six.text_type(args),
                         six.text_type(kwargs)))
                else:
                    method(self.rpc.services, rfs, *args, **kwargs)
                    if not within_batch:
                        self._post_processing(rfs)
            else:
                self._log_error(
                    u'Unrecognized notification from peer: ' +
                    six.text_type(msg))
        except Exception as e:
            self._log_error(e)

    def _handle_response(self, msg):
        msg_id = msg['id']
        promise = self._responses.get(msg_id)
        if promise:
            if 'result' in msg:
                promise.set(msg['result'])
            else:
                promise.set(RpcErrors.error_to_exception(msg['error']))
        else:
            self._log_error(
                u'Unrecognized/expired response from peer: ' +
                six.text_type(msg))

    def _dispatch_batch(self, msgs):
        self._log_info(u'Received batch: ' + six.text_type(msgs))
        rfs = RpcForServices(self.rpc)
        promises = []
        for msg in msgs:
            if 'id' in msg:
                promises.append(self._tasking.spawn_task(self.gid_handlers, self._handle_request, msg, rfs))
            else:
                self._tasking.spawn_task(self.gid_handlers, self._handle_notification, msg, rfs)
        # FIXME mapping a wait not good -> tasker needs .all() and .any()
        results = list(map(lambda p: p.wait(), promises))
        results = list(map(lambda x: x.left, results))
        if results:
            if rfs.aborted:
                self._log_info(
                    'Connection aborted during batch processing.')
                return
            self.rpc.socket_queue.put(results)
            self._log_info(
                u'Sent batch response: ' + six.text_type(results))
        else:
            self._log_info(u'Notification-only batch processed.')
        # FIXME do this with tasker:
        #if not rfs.close_after_response_requested:
        #    for nthread in [t for t in nthreads if t]:
        #        nthread.join()
        if rfs.close_after_response_requested:
            self.rpc.close()
            self._log_info(
                u'RPC closed due to invocation by Request or '
                u'Notification handler.')

    def _handle_batch_response(self, msgs):
        def _extract_msg_content(msg):
            if 'result' in msg:
                return msg['result']
            else:
                return RpcErrors.error_to_exception(msg['error'])

        without_id_msgs = list(filter(lambda x: x.get('id') is None, msgs))
        with_id_msgs = list(filter(lambda x: x.get('id') is not None, msgs))
        resp_map = dict(map(lambda x: (x['id'], x), with_id_msgs))
        msg_ids = set(resp_map.keys())
        resolved = False
        for idtuple, promise in self._batch_responses.items():
            if msg_ids.issubset(set(idtuple)):
                batch_response = []
                for req_id in idtuple:
                    if req_id in resp_map:
                        batch_response.append(
                            _extract_msg_content(resp_map[req_id]))
                    elif without_id_msgs:
                        batch_response.append(
                            _extract_msg_content(without_id_msgs.pop(0)))
                    else:
                        batch_response.append(
                            BsonRpcError(
                                'Peer did not respond to this request!'))
                promise.set(batch_response)
                resolved = True
                break
        if not resolved:
            self._log_error(
                u'Unrecognized/expired batch response from peer: ' +
                six.text_type(msgs))
            
    def _handle_parse_error(self, exception):
        try:
            self.rpc.socket_queue.put(
                self.rpc.definitions.error_response(
                    None, RpcErrors.parse_error, six.text_type(exception)))
        except:
            pass  # Effort made, success not required.
        self._log_error(exception)
        
    def _handle_schema_error(self, msg):
        msg_id = None
        if isinstance(msg.get('id'), (six.string_types, int)):
            msg_id = msg['id']
        self.rpc.socket_queue.put(
            self.rpc.definitions.error_response(
                msg_id, RpcErrors.invalid_request))
        self._log_error(u'Invalid Request: ' + six.text_type(msg))
            
    def _resolve_message_handler(self, msg):
        rpcd = self.rpc.definitions
        dispatch = {
            dict: [
                (rpcd.is_request, self._handle_request, self.gid_handlers),
                (rpcd.is_notification, self._handle_notification, self.gid_handlers),
                (rpcd.is_response, self._handle_response, None),
                (rpcd.is_nil_id_error_response, self._log_error, None),
            ],
            list: [
                (rpcd.is_batch_request, self._dispatch_batch, self.gid_batches),
                (rpcd.is_batch_response, self._handle_batch_response, None),
            ]
        }
        for match_fn, handler_fn, task_category in dispatch.get(type(msg), []):
            if match_fn(msg):
                return handler_fn, task_category
        return self._handle_schema_error, None

    def run(self):
        self._log_info(u'Start RPC message dispatcher.')
        while True:
            try:
                msg = self.rpc.socket_queue.get()
                if msg is None:
                    break
                self._log_info(u'Dispatch message.')
                if isinstance(msg, Exception):
                    self._handle_parse_error(msg)
                else:
                    handler, task_category = self._resolve_message_handler(msg)
                    if task_category:
                        self._tasking.spawn_task(task_category, handler, msg)
                    else:
                        handler(msg)
            except Exception as e:
                self._log_error(e)
        self._log_info(u'Exit RPC message dispatcher.')

    def join(self, timeout=None):
        self._tasking.join(timeout=timeout)
