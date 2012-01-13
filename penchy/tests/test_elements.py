import unittest2

from penchy.tests.util import MockPipelineElement


class PipelineElementHookTest(unittest2.TestCase):
    def setUp(self):
        self.e = MockPipelineElement()
        self.list_ = [23, 42, 5]

    def test_pre_hooks(self):
        self.e.prehooks = [
            lambda: self.list_.__setitem__(0, 1),
            lambda: self.list_.__setitem__(1, 1),
            lambda: self.list_.__setitem__(2, 1)]

        self.e.run()

        self.assertListEqual(self.list_, [1, 1, 1])

    def test_post_hooks(self):
        self.e.posthooks = [
            lambda: self.list_.__setitem__(0, 1),
            lambda: self.list_.__setitem__(1, 1),
            lambda: self.list_.__setitem__(2, 1)]

        self.e.run()

        self.assertListEqual(self.list_, [1, 1, 1])
