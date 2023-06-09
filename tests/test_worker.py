import numpy as np
import unittest
from queue import Queue
from time import sleep
from pympipool import Executor
from pympipool.share.serial import execute_tasks, _cloudpickle_update
from concurrent.futures import Future


def calc(i):
    return np.array(i ** 2)


def mpi_funct(i):
    from mpi4py import MPI
    size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    return i, size, rank


class TestFuturePool(unittest.TestCase):
    def test_pool_serial(self):
        with Executor(cores=1) as p:
            output = p.submit(calc, i=2)
            self.assertEqual(len(p), 1)
            self.assertTrue(isinstance(output, Future))
            self.assertFalse(output.done())
            sleep(1)
            self.assertTrue(output.done())
            self.assertEqual(len(p), 0)
        self.assertEqual(output.result(), np.array(4))

    def test_pool_serial_map(self):
        with Executor(cores=1) as p:
            output = p.map(calc, [1, 2, 3])
        self.assertEqual(list(output), [np.array(1), np.array(4), np.array(9)])

    def test_pool_multi_core(self):
        with Executor(cores=2) as p:
            output = p.submit(mpi_funct, i=2)
            self.assertEqual(len(p), 1)
            self.assertTrue(isinstance(output, Future))
            self.assertFalse(output.done())
            sleep(1)
            self.assertTrue(output.done())
            self.assertEqual(len(p), 0)
        self.assertEqual(output.result(), [(2, 2, 0), (2, 2, 1)])

    def test_pool_multi_core_map(self):
        with Executor(cores=2) as p:
            output = p.map(mpi_funct, [1, 2, 3])
        self.assertEqual(list(output), [[(1, 2, 0), (1, 2, 1)], [(2, 2, 0), (2, 2, 1)], [(3, 2, 0), (3, 2, 1)]])

    def test_execute_task_failed_no_argument(self):
        f = Future()
        q = Queue()
        q.put({"f": calc, 'a': (), "k": {}, "l": f})
        q.put({"c": "close"})
        _cloudpickle_update(ind=1)
        with self.assertRaises(TypeError):
            execute_tasks(
                future_queue=q,
                cores=1,
                oversubscribe=False,
                enable_flux_backend=False
            )

    def test_execute_task_failed_wrong_argument(self):
        f = Future()
        q = Queue()
        q.put({"f": calc, 'a': (), "k": {"j": 4}, "l": f})
        q.put({"c": "close"})
        _cloudpickle_update(ind=1)
        with self.assertRaises(TypeError):
            execute_tasks(
                future_queue=q,
                cores=1,
                oversubscribe=False,
                enable_flux_backend=False
            )

    def test_execute_task(self):
        f = Future()
        q = Queue()
        q.put({"f": calc, 'a': (), "k": {"i": 2}, "l": f})
        q.put({"c": "close"})
        _cloudpickle_update(ind=1)
        execute_tasks(
            future_queue=q,
            cores=1,
            oversubscribe=False,
            enable_flux_backend=False
        )
        self.assertEqual(f.result(), np.array(4))

    def test_execute_task_parallel(self):
        f = Future()
        q = Queue()
        q.put({"f": calc, 'a': (), "k": {"i": 2}, "l": f})
        q.put({"c": "close"})
        _cloudpickle_update(ind=1)
        execute_tasks(
            future_queue=q,
            cores=2,
            oversubscribe=False,
            enable_flux_backend=False
        )
        self.assertEqual(f.result(), [np.array(4), np.array(4)])
