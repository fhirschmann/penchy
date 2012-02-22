from penchy.compat import unittest
from penchy.jobs.elements import Workload, Tool
from penchy.jobs.hooks import Hook
from penchy.tests.util import MockPipelineElement


class PipelineElementHookTest(unittest.TestCase):
    def setUp(self):
        self.e = MockPipelineElement()
        self.list_ = [23, 42, 5]

    def test_pre_hooks(self):
        self.e.hooks = [
            Hook(lambda: self.list_.__setitem__(0, 1)),
            Hook(lambda: self.list_.__setitem__(1, 1)),
            Hook(lambda: self.list_.__setitem__(2, 1))]

        self.e.run()

        self.assertListEqual(self.list_, [1, 1, 1])

    def test_post_hooks(self):
        self.e.hooks = [
            Hook(teardown=lambda: self.list_.__setitem__(0, 1)),
            Hook(teardown=lambda: self.list_.__setitem__(1, 1)),
            Hook(teardown=lambda: self.list_.__setitem__(2, 1))]

        self.e.run()

        self.assertListEqual(self.list_, [1, 1, 1])


class NotRunnableTest(unittest.TestCase):
    def test_throw_exception(self):
        w = Workload()
        t = Tool()
        with self.assertRaises(ValueError):
            w.run()
        with self.assertRaises(ValueError):
            t.run()
