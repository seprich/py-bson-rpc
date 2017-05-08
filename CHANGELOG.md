# Change Log
All notable changes to this project will be documented in this file. This change log follows the conventions of [keepachangelog.com](http://keepachangelog.com/).

## [unreleased]

## [0.2.1] - 2017-05-08
### Fixes
- Fix a memory leak issue.

## [0.2.0] - 2017-03-22
### Added
- Automatic support for both pymongo and pybson bson codecs
  (https://pypi.python.org/pypi/pymongo & https://pypi.python.org/pypi/bson/0.4.6)
- Supports providing custom json codec and custom bson codec implementations via options.

## [0.1.2] - 2016-04-13
### Fixes
- Fix threading unstability issue related to dispatcher thread starting too early.
  Big thanks to [pchocholac](https://github.com/pchocholac) for spotting this issue and contributing the fix.

## [0.1.1] - 2016-01-28
### Fixes
- Previous bug where B/JSONRpc.join did not wait/join dispatcher notification handlers.
  Now join guarantees that all library-spawned threads are joined.
- Bug where giving explicit 'services=None' was broken is fixed to follow API doc.
  (Omitting the parameter is and was working)
- Fixed B/JSONRpc.close() raising Exception.

## [0.1.0] - 2016-01-27
### Initial Version:
- JSON-RPC 2.0 and BSON-RPC library on sockets/gevent.sockets.

[unreleased]: https://github.com/seprich/py-bson-rpc/compare/0.2.0...HEAD
[0.2.0]: https://github.com/seprich/py-bson-rpc/compare/0.1.2...0.2.0
[0.1.2]: https://github.com/seprich/py-bson-rpc/compare/0.1.1...0.1.2
[0.1.1]: https://github.com/seprich/py-bson-rpc/compare/0.1.0...0.1.1
[0.1.0]: https://github.com/seprich/py-bson-rpc/tree/0.1.0
