# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='bsonrpc',
    version='0.1.0',
    description=('Stream transport based JSON-RPC 2.0 and BSON-RPC 2.0 '
                 'library which is agnostic about stream implementation '
                 'allowing TLS on TCP if desired.'),
    long_description=read('README.md'),
    packages=find_packages(exclude=['test', 'examples']),
    keywords='bson json rpc bson-rpc json-rpc bsonrpc jsonrpc',
    author='Jussi Seppälä',
    author_email='richard.seppala@gmail.com',
    url='http://github.com/seprich/py-bson-rpc',
    license='Mozilla Public License, version 2.0',
)
