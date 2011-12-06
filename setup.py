#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

# Version will be replaced by maven!
__version__ = '0.1'

setup(name='penchy',
        version=__version__,
        description='JVM Benchmarking Tool',
        url='http://www.tu-darmstadt.de/',
        packages=find_packages(),
        scripts=['bin/penchy_client', 'bin/penchy_server'],
        install_requires=[
            'argparse',
            'paramiko',
            'pycrypto',
            'rpyc',
            'unittest2',
            ]
        )
