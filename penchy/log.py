"""
This module deals with logging in PenchY.

 .. moduleauthor:: Fabian Hirschmann <fabian@hirschmann.email>
 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import logging
from logging.handlers import RotatingFileHandler


def configure_logging(level=logging.INFO, logfile=None):  # pragma: no cover
    """
    Configure the root logger for our purposes.
    """
    logging.root.setLevel(level)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logging.root.addHandler(ch)

    if logfile:
        ch2 = RotatingFileHandler(logfile, backupCount=10)
        ch2.doRollover()
        ch2.setFormatter(formatter)
        logging.root.addHandler(ch2)

    logging.getLogger('paramiko.transport').setLevel(logging.ERROR)


def configure_for_tests():
    """
    Configure the root logger to be silent.
    """
    logging.root.handlers = []
    logging.root.addHandler(NullHandler())


class NullHandler(logging.Handler):  # pragma: no cover
    """
    Handler that does nothing.
    """
    def handle(self, record):
        pass

    def emit(self, record):
        pass

    def createLock(self):
        self.lock = None
