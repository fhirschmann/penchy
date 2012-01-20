from distutils.core import setup
from setuptools import find_packages
from penchy import __version__

setup(name='penchy',
        version=__version__,
        description='JVM Benchmarking Tool',
        url='http://www.tu-darmstadt.de/',
        packages=['penchy'],
        scripts=[
            'bin/penchy',
            'bin/penchy_test_job,
            'bin/penchy_bootstrap'],
        install_requires=[
            'argparse',
            'paramiko',
            'pycrypto',
            'rpyc',
            'unittest2']
        )
