import os
import json

from penchy.jobs.elements import PipelineElement
from penchy.jobs.dependency import Edge
from penchy.jobs.job import NodeConfiguration, JVMNodeConfiguration
from penchy.jobs.jvms import JVM

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
        self.outputs = [(name, int) for name in names]
        self.out = dict((name, 42) for name in names)

    def __repr__(self):
        return "MockPipelineElement({0}, {1})".format(self.outputs, self.out)

    def _run(self):
        pass

    def check(self):
        pass


def make_jvmnode_config(host=''):
    jvm = JVM('dummy')
    node = NodeConfiguration(host, 22, 'this', 'is', 'a dummy')
    return JVMNodeConfiguration(jvm, node)
