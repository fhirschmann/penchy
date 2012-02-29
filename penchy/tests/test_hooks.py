from penchy.compat import unittest
from penchy.jobs import hooks


class ExecuteHookTest(unittest.TestCase):
    def test_termination(self):
        hook = hooks.ExecuteHook('python')
        hook.setup()
        self.assertIsNone(hook.proc.returncode)
        hook.teardown()
        self.assertEqual(hook.proc.returncode, -15)
