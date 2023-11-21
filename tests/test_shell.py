from unittest import TestCase

from pympipool.shell.executor import ShellStaticExecutor, ShellExecutor


class StaticExecutorTest(TestCase):
    def test_shell_static(self):
        with ShellStaticExecutor() as exe:
            future = exe.submit(["echo", "test"], universal_newlines=True)
            self.assertFalse(future.done())
            self.assertEqual("test\n", future.result())
            self.assertTrue(future.done())

    def test_shell(self):
        with ShellExecutor(max_workers=2) as exe:
            f_1 = exe.submit(["echo", "test_1"], universal_newlines=True)
            f_2 = exe.submit(["echo", "test_2"], universal_newlines=True)
            f_3 = exe.submit(["echo", "test_3"], universal_newlines=True)
            f_4 = exe.submit(["echo", "test_4"], universal_newlines=True)
            self.assertFalse(f_1.done())
            self.assertFalse(f_2.done())
            self.assertFalse(f_3.done())
            self.assertFalse(f_4.done())
            self.assertEqual("test_1\n", f_1.result())
            self.assertEqual("test_2\n", f_2.result())
            self.assertTrue(f_1.done())
            self.assertTrue(f_2.done())
            self.assertFalse(f_3.done())
            self.assertFalse(f_4.done())
            self.assertEqual("test_3\n", f_3.result())
            self.assertEqual("test_4\n", f_4.result())
            self.assertTrue(f_1.done())
            self.assertTrue(f_2.done())
            self.assertTrue(f_3.done())
            self.assertTrue(f_4.done())
