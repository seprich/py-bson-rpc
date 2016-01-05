# py-bson-rpc [![Build Status](https://travis-ci.org/seprich/py-bson-rpc.svg?branch=master)](https://travis-ci.org/seprich/py-bson-rpc)

A Python library for JSON-RPC 2.0 and BSON-RPC on sockets (TCP & TCP+TLS).

| [API doc](http://seprich.github.io/py-bson-rpc/index.html)
| [Change Log](https://github.com/seprich/py-bson-rpc/blob/CHANGELOG.md)
|

PyPI Name: `bsonrpc`


## Features

#### JSON-RPC 2.0

* Full implementation of
  [JSON-RPC 2.0 Specification](http://www.jsonrpc.org/specification)

#### BSON-RPC

* Identical to JSON-RPC 2.0 with following differences:
  * Messages are encoded as [BSON](http://bsonspec.org/spec.html) instead
    of JSON.
  * Protocol identifier is "bsonrpc" instead of "jsonrpc".
  * Batches are not supported since BSON doe not have top-level arrays.
* Benefits over JSON-RPC:
  * Binary data type. No schema gimmicks or size penalties.
  * Datetime data type. Often needed and missing from JSON.

#### Transport

This library works upon python
[`socket.socket`](https://docs.python.org/3.4/library/socket.html)
and [`gevent.socket`](http://www.gevent.org/gevent.socket.html) (\*)
or anything which
[squawks](https://en.wikipedia.org/wiki/Duck_typing) like a socket.
Specifically this library uses `close`, `recv`, `sendall` and `shutdown`
methods of the given socket.

(\*) This library can be configured to use gevent greenlets instead of python
     threads, details in
     [API doc](http://seprich.github.io/py-bson-rpc/index.html#about-threading-model)
     .

The creation of server sockets, accepting client connections or connecting to
servers and all kind of connection management is left outside of this library
in order to provide proper separation of concerns and a freedom of
implementation, e.g. websockets, TCP or TCP with TLS (with or without client
authentication) are all equally viable stream connection providers upon which
this library builds the RPC layer.

For JSON-RPC there exists several "framing" methods for identifying message
boundaries in the incoming data stream. This library comes with a direct support
for the following methods:
* [frameless](https://en.wikipedia.org/wiki/JSON_Streaming#Concatenated_JSON)
  method relies on the capability of parser recognizing message boundaries and
  more easily end up in irrecoverable state in case of malformed message than
  other framing methods.
* [rfc-7464](https://tools.ietf.org/html/rfc7464) where each JSON message is
  prefixed with Record Separator (0x1E) and ended with Line Feed (0x0A)
* [Netstring](http://cr.yp.to/proto/netstrings.txt)

In order to use some other than one of the above mentioned framing methods
you can provide your own `extract_message` and `into_frame` functions for this
library. See API documentation for exact details and definitions.

#### Concurrency

The JSONRpc/BSONRpc objects can be set to use either:
* Python threads (default) or
* [gevent](http://www.gevent.org/index.html) for
  more efficient concurrency.

#### Logging

Internal dispatcher utilizes python default `logging` library to log:
* Unexpected events / non-rpc-dispatchable exceptions -> Logger.error
* Basic dispatcher events -> Logger.info

## Quickstart

#### Minimalistic Example
##### Server
```python
import socket
from bsonrpc import JSONRpc
from bsonrpc import request, service_class

# Class providing functions for the client to use:
@service_class
class ServerServices(object):

  @request
  def swapper(self, txt):
    return ''.join(reversed(list(txt)))

# Quick-and-dirty TCP Server:
ss = socket.socket(socket.AF_INET, socket.SOCKET_STREAM)
ss.bind(('localhost', 6000))
ss.listen(10)

while True:
  s, _ = ss.accept()
  # JSONRpc object spawns internal thread to serve the connection.
  JSONRpc(s, ServerServices())
```

##### Client
```python
import socket
from bsonrpc import JSONRpc

# Cut-the-corners TCP Client:
s = socket.socket(socket.AF_INET, socket.SOCKET_STREAM)
s.connect(('localhost', 6000))

rpc = JSONRpc(s)
server = rpc.get_peer_proxy()
# Execute in server:
result = server.swapper('Hello World!')
# "!dlroW olleH"
print(result)
rpc.close() # Closes the socket 's' also
```

#### Example with more Features
##### Server
```python
import gevent.socket as gsocket
from bsonrpc import JSONRpc, ThreadingModel
from bsonrpc import rpc_request, request, service_class

@service_class
class ServerServices(object):

  @request
  def echo_times(self, txt, n):
    return txt * n

  @rpc_request
  def long_process(self, rpc, a, b, c):
    print(rpc.client_info)
    # 2 ways to send notifications:
    rpc.invoke_notification('report_progress', 'Stage 1')
    client = rpc.get_peer_proxy()
    client.n.report_progress('Stage 2')
    # Make a request to client, why not:
    result = client.swapper('TestinG')
    print(result) # -> "GnitseT"
    return a * b * c

# Quick-and-dirty TCP Server:
ss = gsocket.socket(gsocket.AF_INET, gsocket.SOCKET_STREAM)
ss.bind(('localhost', 6000))
ss.listen(10)

while True:
  s, addr = ss.accept()
  JSONRpc(s,
          ServerServices(),
          client_info=addr,
          threading_model=ThreadingModel.GEVENT,
          concurrent_request_handling=ThreadingModel.GEVENT)
```

##### Client
```python
import socket
from bsonrpc import BatchBuilder, JSONRpc
from bsonrpc import request, notification, service_class

@service_class
class ClientServices(object):

  @request
  def swapper(self, txt):
    return ''.join(reversed(list(txt)))

  @notification
  def report_progress(self, txt):
    print('Msg from server: ' + txt)

# Cut-the-corners TCP Client:
s = socket.socket(socket.AF_INET, socket.SOCKET_STREAM)
s.connect(('localhost', 6000))

rpc = JSONRpc(s, ClientServices())
# Batch call:
bb = BatchBuilder()
bb.echo_times('-hello-', 2)
bb.echo_times('-world-', 1)
batch_result = rpc.batch_call(bb)
print(batch_result) # -> ['-hello--hello-', '-world-']
server = rpc.get_peer_proxy()
print(server.long_process(2, 3, 4))
# -> Msg from server: Stage 1
# -> Msg from server: Stage 2
# -> 24
rpc.close() # Closes the socket 's' also
```

## TODO

* Log sanitizer hook - allow custom filters to prevent sensitive info from
  being logged.
* Message in- and out- processor hooks. -> Mangle the messages beyond
  recognition if desired.

## License

Copyright © 2016 Jussi Seppälä

All Source Code Forms in this repository are subject to the
terms of the Mozilla Public License, v.
2.0. If a copy of the MPL was not
distributed with this file, You can
obtain one at
http://mozilla.org/MPL/2.0/.
