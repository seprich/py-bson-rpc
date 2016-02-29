.. py-bson-rpc documentation master file, created by
   sphinx-quickstart on Thu Jan  7 23:52:34 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


.. toctree::
   :maxdepth: 2


bsonrpc - JSON/BSON RPC
=======================

.. automodule:: bsonrpc

Install with pip3

And use:
    ``import bsonrpc``


JSONRpc Objects
===============

.. autoclass:: bsonrpc.JSONRpc
   :show-inheritance:
   :members:
   :inherited-members:
   :special-members: __init__


BSONRpc Objects
===============

.. autoclass:: bsonrpc.BSONRpc
   :show-inheritance:
   :members:
   :inherited-members:
   :special-members: __init__


Providing Services
==================

In order to provide remote callable functions the `JSONRpc Objects`_ and
`BSONRpc Objects`_ do expect to get a ``bsonrpc.service_class``-decorated
Class instance as an argument. Use the decorators introduced below
to announce methods either as request handlers or notification handlers.

Decorators
----------

.. autofunction:: bsonrpc.service_class

.. autofunction:: bsonrpc.request

.. autofunction:: bsonrpc.notification

.. autofunction:: bsonrpc.rpc_request

.. autofunction:: bsonrpc.rpc_notification


About rpc-reference
-------------------

The JSONRpc/BSONRpc reference object given at runtime to ``rpc_request``
and ``rpc_notification`` -decorated methods enables accessing of
JSONRpc/BSONRpc-methods from service-methods, with following differences:

* ``.close()`` is renamed to ``.abort()`` to highlight the abnormal nature
  of discontinued request handling. Causes the return value of the request
  handler to be discarded.
* ``.close_after_response()`` (Takes no arguments) is available. This will
  trigger the connection to be closed right after the return value turned
  into a response message has been sent to the peer node.


Service Provider Example
------------------------

.. code-block:: python

  from bsonrpc import service_class, request, rpc_request, notification

  @service_class
  class MyServices(object):

      # __init__  etc..

      @request
      def revert(self, txt):
          return ''.join(reversed(list(txt)))

      @rpc_request
      def calculate(self, rpc, a, b, c):
          rpc.invoke_notification('report_progress', '.')
          rpc.invoke_notification('report_progress', '..')
          return a * b * c

      @rpc_request
      def final_message(self, rpc, txt):
          # Custom attribute 'my_custom_label', set via options
          self.log(rpc.my_custom_label + txt)
          rpc.close_after_response()
          return 'Good Bye!'

      @notification
      def log(self, fmt, *args):
          print('From peer: ' + fmt % args)


bsonrpc.framing
===============

.. automodule:: bsonrpc.framing


About Threading Model
=====================

This library contains concurrent execution threads for:

1. Decoder receiving bytes from socket, extracting and decoding messages
   to python data objects and putting them to queue for dispatcher to consume.
2. Dispatcher consuming messages from the socket-queue, dispatching incoming
   responses to local waiter(s), requests and notifications to service handlers
   via selected strategy (3 & 4) and spawning batch collectors to handle
   bathces.
3. To handle an incoming request the Dispatcher can either execute the responsible
   request handler without spawning any threads or can spawn a thread to execute
   that handler, depending on the selected ``concurrent_request_handling``
   -strategy.

   If a handler is executed without threading the Dispatcher cannot take any new
   messages for processing from the queue until the handler has returned. Spawning
   allows simultaneous processing of multiple requests which is usually desirable.
   Control flow is not any less deterministic as it is fully controlled by the
   rpc peer node using the service interface.
4. In identical way the selected ``concurrent_notification_handling``-strategy will
   determine notification handler spawning.


For basic concurrency (points 1 & 2 above) this library can be configured to use
either basic python threads or *gevent* (*) lib greenlets. This is done with
the ``threading_model`` -option.

The following option combinations have been unittested:

========================== =============================== ====================================
threading_model            concurrent_request_handling     concurrent_notification_handling
========================== =============================== ====================================
ThreadingModel.THREADS     ThreadingModel.THREADS          None
ThreadingModel.THREADS     ThreadingModel.THREADS          ThreadingModel.THREADS
ThreadingModel.GEVENT      ThreadingModel.GEVENT           None
ThreadingModel.GEVENT      ThreadingModel.GEVENT           ThreadingModel.GEVENT
========================== =============================== ====================================

(*) see requirements.txt for minimal version requirements.
