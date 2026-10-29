import unittest
from owl.runtime import run_task


class RuntimeTests(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            run_task(" ")

    def test_large(self):
        with self.assertRaises(ValueError):
            run_task("x" * 16001)

    def test_unsupported_mode(self):
        with self.assertRaises(ValueError):
            run_task("hello", mode="exec")
