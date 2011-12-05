#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(name='Penchy',
        version='0.1',
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
