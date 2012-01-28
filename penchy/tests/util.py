"""
This module provides tools to make testing easier.

 .. moduleauthor:: Michael Markert <markert.michael@googlemail.com>

 :copyright: PenchY Developers 2011-2012, see AUTHORS
 :license: MIT License, see LICENSE
"""
import os
import json

from penchy.jobs.elements import PipelineElement
from penchy.jobs.job import NodeSetting, SystemComposition
from penchy.jobs.dependency import Edge
from penchy.jobs.jvms import JVM
from penchy.jobs.typecheck import Types

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def get_json_data(name):
    """
    Return the content of the json data file with name.

    :param name: name of the json data file without extension
    :returns: content of json file
    """
    with open(os.path.join(TEST_DATA_DIR, name + '.json')) as f:
        ob = json.load(f)
    return ob


def make_edge(sink, map_):
    return Edge(MockPipelineElement(x[0] for x in map_), sink, map_)


class MockPipelineElement(PipelineElement):
    def __init__(self, names=None):
        super(MockPipelineElement, self).__init__()

        names = [x for x in names] if names is not None else ()
        self.outputs = Types(*[(name, int) for name in names])
        self.out = dict((name, 42) for name in names)

    def __repr__(self):
        return "MockPipelineElement({0}, {1})".format(self.outputs, self.out)

    def __eq__(self, other):
        return self.outputs == other.outputs and self.out == other.out

    def _run(self, *args, **kwargs):
        pass

    def check(self):
        pass


def make_system_composition(host=''):
    jvm = JVM('dummy')
    node = NodeSetting(host, 22, 'this', 'is', 'a dummy')
    return SystemComposition(jvm, node)
