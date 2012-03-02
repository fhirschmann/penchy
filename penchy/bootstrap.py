#!/usr/bin/env python
"""
This is the bootstrap client.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschm.net>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import os
import sys
import logging
import signal
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

from subprocess import Popen, PIPE


log = logging.getLogger('penchy.bootstrap')


def load_penchy(path):
    """
    This loads :class:`penchy.client.Client` from
    a zip file or directory.

    :param path: zip or directory to load from
    :type path: string
    :returns: PenchY client
    :rtype: :class:`penchy.client.Client`
    """
    sys.path.insert(0, os.path.abspath(path))
    from penchy.client import Client
    import penchy
    log.info('Running PenchY %s from %s' % (penchy.__version__, penchy.__file__))
    return Client


def find_penchy_zip(source):
    """
    This will try to find the path to the penchy zip file.

    Raises OSError if the zip cannot be found.

    :param source: source to look for the zip file for
    :type source: string
    :returns: path to zip file
    :rtype: string
    """
    for path in source.split(os.linesep):
        if path.endswith('-py.zip'):
            if os.path.isfile(path):
                return path

    raise OSError('PenchY zip could not be found')


def install_penchy():
    """
    This function will execute maven, install PenchY and return
    maven's output.

    :returns: maven output
    :rtype: string
    """
    log.debug('Installing/updating PenchY using maven')
    proc = Popen(['mvn', '-f', 'bootstrap.pom', 'install'], stdout=PIPE)
    signal.signal(signal.SIGTERM, lambda num, frame: proc.send_signal(num))
    stdout, _ = proc.communicate()
    stdout = stdout.decode('utf-8')
    log.debug(stdout)
    return stdout


def build_classpath():
    """
    This function will build the classpath using bootstrap.pom

    :returns: maven output
    :rtype: string
    """
    log.debug('Building maven classpath')
    proc2 = Popen(['mvn', '-f', 'bootstrap.pom', 'dependency:build-classpath'],
            stdout=PIPE)
    stdout, _ = proc2.communicate()
    return stdout


def main(job, config, identifier, loglevel=logging.INFO, load_from=None):
    """
    This method starts the bootstrap client.

    A valid bootstrap.pom in the current working directory is
    expected!

    :param job: filename of job to execute
    :type job: string
    :param config: config file to use
    :type config: string
    :param identifier: identifier for this node
    :type identifier: string
    :param loglevel: loglevel to use
    :type loglevel: int
    :param load_from: this will load PenchY from this path instead of
                      running it from the maven repository
    :type load_from: string
    """
    if load_from:
        Client = load_penchy(load_from)
    else:
        install_penchy()
        maven_output = build_classpath()
        penchy_zip = find_penchy_zip(maven_output)
        Client = load_penchy(penchy_zip)

    client = Client(job, config, identifier, loglevel)
    client.run()


if __name__ == '__main__':
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    ch = RotatingFileHandler('penchy_bootstrap.log', backupCount=10)
    ch.doRollover()
    ch.setFormatter(formatter)
    log.addHandler(ch)

    try:
        with open('penchy.pid', 'w') as pidfile:
            pidfile.write(str(os.getpid()))

        parser = OptionParser()
        parser.add_option('--load-from', action='store', type='string',
                dest='load_from', help='load PenchY from this location instead')
        parser.add_option('--loglevel', action='store', type='int',
                dest='loglevel', help='loglevel', default=logging.INFO)
        opts, args = parser.parse_args()
        log.setLevel(opts.loglevel)

        main(*args, load_from=opts.load_from, loglevel=opts.loglevel)
    except Exception as err:
        log.exception('Exception occured while executing PenchY:')
        sys.exit(1)
