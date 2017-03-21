# -*- coding: utf-8 -*-
import os
import re

from setuptools import setup, find_packages


def read(*names):
    with open(os.path.join(os.path.dirname(__file__), *names)) as fp:
        return fp.read()


def get_version():
    filecontent = read('bsonrpc', '__init__.py')
    version_match = re.search(r'^__version__ *= *[\'\"]([^\'\"]+)[\'\"]',
                              filecontent, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    name='bsonrpc',
    version=get_version(),
    description=('JSON-RPC 2.0 and BSON-RPC 2.0 library for socket '
                 'transports. Supports gevent.'),
    long_description=read('doc', 'pypi-readme.rst'),
    url='http://github.com/seprich/py-bson-rpc',
    author='Jussi Seppälä',
    author_email='richard.seppala@gmail.com',
    license='Mozilla Public License, version 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='bson json rpc bson-rpc json-rpc bsonrpc jsonrpc gevent',
    packages=find_packages(exclude=['contrib', 'doc', 'tests']),
    install_requires=['six'],
)
