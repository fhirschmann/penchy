#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages

setup(name='Penchy',
        version='0.1',
        description='JVM Benchmarking Tool',
        url='http://www.tu-darmstadt.de/',
        packages=find_packages(),
        scripts=['scripts/penchy_client', 'scripts/penchy_server'],
        install_requires=[
            'argparse',
            'paramiko',
            'pyrcrypto',
            'rpyc',
            'unittest2',
            ]
        )
