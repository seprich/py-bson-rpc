# py-bson-rpc

A python library for JSON-RPC 2.0 and BSON-RPC on sockets (TCP & TCP+TLS).

**Under development**

| [API doc](http://seprich.github.io/py-bson-rpc/index.html)
|

## Features

#### JSON-RPC 2.0

#### BSON-RPC

#### Transport

This library works upon python
[`socket.socket`](https://docs.python.org/3.4/library/socket.html)
or anything which
[squawks](https://en.wikipedia.org/wiki/Duck_typing) like a socket.
Specifically this library uses `close`, `recv`, `sendall` and `shutdown`
methods of the given socket.

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
library. See API documentation for exact definitions.

#### Logging

## Quickstart


## License

Copyright © 2016 Jussi Seppälä

All Source Code Forms in this repository are subject to the
terms of the Mozilla Public License, v.
2.0. If a copy of the MPL was not
distributed with this file, You can
obtain one at
http://mozilla.org/MPL/2.0/.
