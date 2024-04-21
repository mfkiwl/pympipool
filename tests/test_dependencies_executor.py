import unittest
from time import sleep

from pympipool.dependencies import ExecutorWithDependencies
from pympipool.shared.executorbase import cloudpickle_register


def add_function(parameter_1, parameter_2):
    sleep(0.2)
    return parameter_1 + parameter_2


class TestExecutorWithDependencies(unittest.TestCase):
    def test_executor(self):
        with ExecutorWithDependencies(max_cores=1, backend="mpi", hostname_localhost=True) as exe:
            cloudpickle_register(ind=1)
            future_1 = exe.submit(add_function, 1, parameter_2=2)
            future_2 = exe.submit(add_function, 1, parameter_2=future_1)
            self.assertEqual(future_2.result(), 4)
