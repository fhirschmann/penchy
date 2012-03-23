from penchy.compat import unittest
from penchy.jobs.typecheck import Types, TypeCheckError
from penchy.tests.util import MockPipelineElement


class CheckArgsTest(unittest.TestCase):
    def setUp(self):
        super(CheckArgsTest, self).setUp()

        self.p = MockPipelineElement()
        self.inputs = Types(('foo', str),
                            ('bar', list, int))

        self.d = {'foo' : '23', 'bar' : list(range(5))}

    def test_malformed_types(self):
        for t in ((1, str),
                 (1, list, str),
                 ('bar', str, 2),
                 ('baz', 2, list),
                 ()):
            with self.assertRaises(AssertionError):
                Types(t)

    def test_wrong_type(self):
        self._raising_error_on_replacement(TypeCheckError,
                                           (('foo', 23),
                                            ('foo', ['23']),
                                            ('bar', 42)))

    def test_wrong_subtype(self):
        self._raising_error_on_replacement(TypeCheckError,
                                           (('bar', ['23']),
                                            ('bar', [(), ()])))

    def test_missing_arg(self):
        self._raising_error_on_deletion(TypeCheckError,
                                        (('foo'),
                                         ('bar'),
                                         (['foo', 'bar']),
                                         (['foo', 'bar'])))

    def test_unused_input_count(self):
        self.d['baz'] = 42
        self.d['bad'] = 23
        self.assertEqual(self.inputs.check_input(self.d), 2)

    def test_fully_used_input_count(self):
        self.assertEqual(self.inputs.check_input(self.d), 0)

    def test_disabled_checking(self):
        # d contains 2 unused inputs
        self.assertEqual(Types().check_input(self.d), 0)

    def test_subtype_of_dict(self):
        inputs = Types(('foo', dict, int),
                       ('bar', dict, list, int))
        self.assertEqual(inputs.check_input({'foo' : dict(a=1, b=2),
                                             'bar' : dict(a=[1], b=[2])})
                         , 0)
        with self.assertRaises(TypeCheckError):
            self.inputs.check_input({'foo' : dict(a=1, b=2),
                                     'bar' : dict(a=1, b=2)})

    def _raising_error_on_deletion(self, error, deletions):
        for del_ in deletions:
            with self.assertRaises(error):
                d = self.d.copy()
                if not isinstance(del_, (list, tuple)):
                    del_ = [del_]
                for del__ in del_:
                    d.pop(del__, None)
                self.inputs.check_input(d)

    def _raising_error_on_replacement(self, error, replacements):
        for k, v in replacements:
            with self.assertRaises(error):
                d = self.d.copy()
                d[k] = v
                self.inputs.check_input(d)


class SinkCheckTest(unittest.TestCase):
    def test_valid_input(self):
        sink = Types()
        self.assertTrue(sink.check_sink([('foo', [('foo', 'bar')]),
                                         ('baz', [('baz', 'bad')])]))

    def test_overwritten_input(self):
        sink = Types()
        self.assertFalse(sink.check_sink([('foo', [('foo', 'bar')]),
                                          ('baz', [('baz', 'bar')])]))

    def test_inputs_not_statisfied(self):
        sink = Types(('foo', object))
        self.assertFalse(sink.check_sink([('foo', [('foo', 'bar'), ('baz', 'quux')])]))

    def test_internal_inputs_not_statisfied(self):
        sink = Types(('bar', object), (':quux:', object))
        self.assertTrue(sink.check_sink([('foo', [('foo', 'bar')])]))
