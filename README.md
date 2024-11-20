# executorlib
[![Unittests](https://github.com/pyiron/executorlib/actions/workflows/unittest-openmpi.yml/badge.svg)](https://github.com/pyiron/executorlib/actions/workflows/unittest-openmpi.yml)
[![Coverage Status](https://coveralls.io/repos/github/pyiron/executorlib/badge.svg?branch=main)](https://coveralls.io/github/pyiron/executorlib?branch=main)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/pyiron/executorlib/HEAD?labpath=notebooks%2Fexamples.ipynb)

Up-scale python functions for high performance computing (HPC) with executorlib. 

## Key Features
* **Up-scale your Python functions beyond a single computer.** - executorlib extends the [Executor interface](https://docs.python.org/3/library/concurrent.futures.html#executor-objects)
  from the Python standard library and combines it with job schedulers for high performance computing (HPC) including 
  the [Simple Linux Utility for Resource Management (SLURM)](https://slurm.schedmd.com) and [flux](http://flux-framework.org). 
  With this combination executorlib allows users to distribute their Python functions over multiple compute nodes.
* **Parallelize your Python program one function at a time** - executorlib allows users to assign dedicated computing
  resources like CPU cores, threads or GPUs to one Python function call at a time. So you can accelerate your Python 
  code function by function.
* **Permanent caching of intermediate results to accelerate rapid prototyping** - To accelerate the development of 
  machine learning pipelines and simulation workflows executorlib provides optional caching of intermediate results for 
  iterative development in interactive environments like jupyter notebooks.

## Examples
The Python standard library provides the [Executor interface](https://docs.python.org/3/library/concurrent.futures.html#executor-objects)
with the [ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor) and the 
[ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) for parallel 
execution of Python functions on a single computer. executorlib extends this functionality to distribute Python 
functions over multiple computers within a high performance computing (HPC) cluster. This can be either achieved by 
submitting each function as individual job to the HPC job scheduler - [HPC Submission Mode]() - or by requesting a 
compute allocation of multiple nodes and then distribute the Python functions within this allocation - [HPC Allocation Mode](). 
Finally, to accelerate the development process executorlib also provides a - [Local Mode]() - to use the executorlib 
functionality on a single workstation for testing. Starting with the [Local Mode]() set by setting the backend parameter
to local - `backend="local"`:
```python
from executorlib import Executor


with Executor(backend="local") as exe:
    future_lst = [exe.submit(sum, [i, i]) for i in range(1, 5)]
    print([f.result() for f in future_lst])
```
In the same way executorlib can also execute Python functions which use additional computing resources, like multiple 
CPU cores, CPU threads or GPUs. For example if the Python function internally uses the Message Passing Interface (MPI) 
via the [mpi4py](https://mpi4py.readthedocs.io) Python libary: 
```python
from executorlib import Executor


def calc(i):
    from mpi4py import MPI

    size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    return i, size, rank


with Executor(backend="local") as exe:
    fs = exe.submit(calc, 3, resource_dict={"cores": 2})
    print(fs.result())
```
The additional `resource_dict` parameter defines the computing resources allocated to the execution of the submitted 
Python function. In addition to the compute cores `cores`, the resource dictionary can also define the threads per core
as `threads_per_core`, the GPUs per core as `gpus_per_core`, the working directory with `cwd`, the option to use the
OpenMPI oversubscribe feature with `openmpi_oversubscribe` and finally for the [Simple Linux Utility for Resource 
Management (SLURM)](https://slurm.schedmd.com) queuing system the option to provide additional command line arguments 
with the `slurm_cmd_args` parameter - [resource dictionary]().

This flexibility to assign computing resources on a per-function-call basis simplifies the up-scaling of Python programs.
Only the part of the Python functions which benefit from parallel execution are implemented as MPI parallel Python 
funtions, while the rest of the program remains serial. 

The same function can be submitted to the [SLURM](https://slurm.schedmd.com) queuing by just changing the `backend` 
parameter to `slurm_submission`. The rest of the example remains the same, which highlights how executorlib accelerates
the rapid prototyping and up-scaling of HPC Python programs. 
```python
from executorlib import Executor


def calc(i):
    from mpi4py import MPI

    size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    return i, size, rank


with Executor(backend="slurm_submission") as exe:
    fs = exe.submit(calc, 3, resource_dict={"cores": 2})
    print(fs.result())
```
In this case the [Python simple queuing system adapter (pysqa)](https://pysqa.readthedocs.io) is used to submit the 
`calc()` function to the [SLURM](https://slurm.schedmd.com) job scheduler and request an allocation with two CPU cores 
for the execution of the function - [HPC Submission Mode](). In the background the [sbatch](https://slurm.schedmd.com/sbatch.html) 
command is used to request the allocation to execute the Python function. 

Within a given [SLURM](https://slurm.schedmd.com) allocation executorlib can also be used to assign a subset of the 
available computing resources to execute a given Python function. In terms of the [SLURM](https://slurm.schedmd.com) 
commands, this functionality internally uses the [srun](https://slurm.schedmd.com/srun.html) command to receive a subset
of the resources of a given queuing system allocation. 
```python
from executorlib import Executor


def calc(i):
    from mpi4py import MPI

    size = MPI.COMM_WORLD.Get_size()
    rank = MPI.COMM_WORLD.Get_rank()
    return i, size, rank


with Executor(backend="slurm_allocation") as exe:
    fs = exe.submit(calc, 3, resource_dict={"cores": 2})
    print(fs.result())
```
In addition, to support for [SLURM](https://slurm.schedmd.com) executorlib also provides support for the hierarchical 
[flux](http://flux-framework.org) job scheduler. The [flux](http://flux-framework.org) job scheduler is developed at 
[Larwence Livermore National Laboratory](https://computing.llnl.gov/projects/flux-building-framework-resource-management)
to address the needs for the up-coming generation of Exascale computers. Still even on traditional HPC clusters the 
hierarchical approach of the [flux](http://flux-framework.org) is beneficial to distribute hundreds of tasks within a
given allocation. Even when [SLURM](https://slurm.schedmd.com) is used as primary job scheduler of your HPC, it is 
recommended to use [SLURM with flux]() as hierarchical job scheduler within the allocations. 

## Documentation
* [Installation](https://executorlib.readthedocs.io/en/latest/installation.html)
  * [Compatible Job Schedulers](https://executorlib.readthedocs.io/en/latest/installation.html#compatible-job-schedulers)
  * [executorlib with Flux Framework](https://executorlib.readthedocs.io/en/latest/installation.html#executorlib-with-flux-framework)
  * [Test Flux Framework](https://executorlib.readthedocs.io/en/latest/installation.html#test-flux-framework)
  * [Without Flux Framework](https://executorlib.readthedocs.io/en/latest/installation.html#without-flux-framework)
* [Examples](https://executorlib.readthedocs.io/en/latest/examples.html)
  * [Compatibility](https://executorlib.readthedocs.io/en/latest/examples.html#compatibility)
  * [Resource Assignment](https://executorlib.readthedocs.io/en/latest/examples.html#resource-assignment)
  * [Data Handling](https://executorlib.readthedocs.io/en/latest/examples.html#data-handling)
  * [Up-Scaling](https://executorlib.readthedocs.io/en/latest/examples.html#up-scaling)
  * [Coupled Functions](https://executorlib.readthedocs.io/en/latest/examples.html#coupled-functions)
  * [SLURM Job Scheduler](https://executorlib.readthedocs.io/en/latest/examples.html#slurm-job-scheduler) 
  * [Workstation Support](https://executorlib.readthedocs.io/en/latest/examples.html#workstation-support)
* [Development](https://executorlib.readthedocs.io/en/latest/development.html)
  * [Contributions](https://executorlib.readthedocs.io/en/latest/development.html#contributions)
  * [License](https://executorlib.readthedocs.io/en/latest/development.html#license)
  * [Integration](https://executorlib.readthedocs.io/en/latest/development.html#integration)
