#!/usr/bin/env python

from collections import namedtuple


NodeConfig = namedtuple('NodeConfig', ['host', 'ssh_port', 'username', 'path'])
