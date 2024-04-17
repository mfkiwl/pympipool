import os
import shutil
from typing import Optional
from ._version import get_versions
from pympipool.mpi.executor import PyMPIExecutor, PyMPIStepExecutor
from pympipool.shared.interface import SLURM_COMMAND
from pympipool.shell.executor import SubprocessExecutor
from pympipool.shell.interactive import ShellExecutor
from pympipool.slurm.executor import PySlurmExecutor, PySlurmStepExecutor

try:  # The PyFluxExecutor requires flux-core to be installed.
    from pympipool.flux.executor import PyFluxExecutor, PyFluxStepExecutor

    flux_installed = "FLUX_URI" in os.environ
except ImportError:
    flux_installed = False
    pass

# The PySlurmExecutor requires the srun command to be available.
slurm_installed = shutil.which(SLURM_COMMAND) is not None


__version__ = get_versions()["version"]


class Executor:
    """
    The pympipool.Executor leverages either the message passing interface (MPI), the SLURM workload manager or preferable
    the flux framework for distributing python functions within a given resource allocation. In contrast to the
    mpi4py.futures.MPIPoolExecutor the pympipool.Executor can be executed in a serial python process and does not
    require the python script to be executed with MPI. It is even possible to execute the pympipool.Executor directly in
    an interactive Jupyter notebook.

    Args:
        max_cores (int): defines the number cores which can be used in parallel
        cores_per_worker (int): number of MPI cores to be used for each function call
        threads_per_core (int): number of OpenMP threads to be used for each function call
        gpus_per_worker (int): number of GPUs per worker - defaults to 0
        oversubscribe (bool): adds the `--oversubscribe` command line flag (OpenMPI only) - default False
        cwd (str/None): current working directory where the parallel python task is executed
        hostname_localhost (boolean): use localhost instead of the hostname to establish the zmq connection. In the
                                      context of an HPC cluster this essential to be able to communicate to an
                                      Executor running on a different compute node within the same allocation. And
                                      in principle any computer should be able to resolve that their own hostname
                                      points to the same address as localhost. Still MacOS >= 12 seems to disable
                                      this look up for security reasons. So on MacOS it is required to set this
                                      option to true
        backend (str): Switch between the different backends "flux", "mpi" or "slurm". Alternatively, when "auto"
                       is selected (the default) the available backend is determined automatically.
        block_allocation (boolean): To accelerate the submission of a series of python functions with the same resource
                                    requirements, pympipool supports block allocation. In this case all resources have
                                    to be defined on the executor, rather than during the submission of the individual
                                    function.
        init_function (None): optional function to preset arguments for functions which are submitted later

    Examples:
        ```
        >>> import numpy as np
        >>> from pympipool import Executor
        >>>
        >>> def calc(i, j, k):
        >>>     from mpi4py import MPI
        >>>     size = MPI.COMM_WORLD.Get_size()
        >>>     rank = MPI.COMM_WORLD.Get_rank()
        >>>     return np.array([i, j, k]), size, rank
        >>>
        >>> def init_k():
        >>>     return {"k": 3}
        >>>
        >>> with Executor(cores=2, init_function=init_k) as p:
        >>>     fs = p.submit(calc, 2, j=4)
        >>>     print(fs.result())
        [(array([2, 4, 3]), 2, 0), (array([2, 4, 3]), 2, 1)]
        ```
    """

    def __init__(
        self,
        max_cores: int = 1,
        cores_per_worker: int = 1,
        threads_per_core: int = 1,
        gpus_per_worker: int = 0,
        oversubscribe: bool = False,
        cwd: Optional[str] = None,
        executor=None,
        hostname_localhost: bool = False,
        backend="auto",
        block_allocation: bool = True,
        init_function: Optional[callable] = None,
    ):
        # Use __new__() instead of __init__(). This function is only implemented to enable auto-completion.
        pass

    def __new__(
        cls,
        max_cores: int = 1,
        cores_per_worker: int = 1,
        threads_per_core: int = 1,
        gpus_per_worker: int = 0,
        oversubscribe: bool = False,
        cwd: Optional[str] = None,
        executor=None,
        hostname_localhost: bool = False,
        backend: str = "auto",
        block_allocation: bool = False,
        init_function: Optional[callable] = None,
    ):
        """
        Instead of returning a pympipool.Executor object this function returns either a pympipool.mpi.PyMPIExecutor,
        pympipool.slurm.PySlurmExecutor or pympipool.flux.PyFluxExecutor depending on which backend is available. The
        pympipool.flux.PyFluxExecutor is the preferred choice while the pympipool.mpi.PyMPIExecutor is primarily used
        for development and testing. The pympipool.flux.PyFluxExecutor requires flux-core from the flux-framework to be
        installed and in addition flux-sched to enable GPU scheduling. Finally, the pympipool.slurm.PySlurmExecutor
        requires the SLURM workload manager to be installed on the system.

        Args:
            max_cores (int): defines the number cores which can be used in parallel
            cores_per_worker (int): number of MPI cores to be used for each function call
            threads_per_core (int): number of OpenMP threads to be used for each function call
            gpus_per_worker (int): number of GPUs per worker - defaults to 0
            oversubscribe (bool): adds the `--oversubscribe` command line flag (OpenMPI only) - default False
            cwd (str/None): current working directory where the parallel python task is executed
            hostname_localhost (boolean): use localhost instead of the hostname to establish the zmq connection. In the
                                      context of an HPC cluster this essential to be able to communicate to an
                                      Executor running on a different compute node within the same allocation. And
                                      in principle any computer should be able to resolve that their own hostname
                                      points to the same address as localhost. Still MacOS >= 12 seems to disable
                                      this look up for security reasons. So on MacOS it is required to set this
                                      option to true
            backend (str): Switch between the different backends "flux", "mpi" or "slurm". Alternatively, when "auto"
                           is selected (the default) the available backend is determined automatically.
            block_allocation (boolean): To accelerate the submission of a series of python functions with the same
                                        resource requirements, pympipool supports block allocation. In this case all
                                        resources have to be defined on the executor, rather than during the submission
                                        of the individual function.
            init_function (None): optional function to preset arguments for functions which are submitted later

        """
        if not block_allocation and init_function is not None:
            raise ValueError("")
        if backend not in ["auto", "mpi", "slurm", "flux"]:
            raise ValueError(
                'The currently implemented backends are ["flux", "mpi", "slurm"]. '
                'Alternatively, you can select "auto", the default option, to automatically determine the backend. But '
                + backend
                + " is not a valid choice."
            )
        elif backend == "flux" or (backend == "auto" and flux_installed):
            if oversubscribe:
                raise ValueError(
                    "Oversubscribing is not supported for the pympipool.flux.PyFLuxExecutor backend."
                    "Please use oversubscribe=False instead of oversubscribe=True."
                )
            if block_allocation:
                return PyFluxExecutor(
                    max_workers=int(max_cores / cores_per_worker),
                    cores_per_worker=cores_per_worker,
                    threads_per_core=threads_per_core,
                    gpus_per_worker=gpus_per_worker,
                    init_function=init_function,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
            else:
                return PyFluxStepExecutor(
                    max_cores=max_cores,
                    cores_per_worker=cores_per_worker,
                    threads_per_core=threads_per_core,
                    gpus_per_worker=gpus_per_worker,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
        elif backend == "slurm" or (backend == "auto" and slurm_installed):
            if block_allocation:
                return PySlurmExecutor(
                    max_workers=int(max_cores / cores_per_worker),
                    cores_per_worker=cores_per_worker,
                    threads_per_core=threads_per_core,
                    gpus_per_worker=gpus_per_worker,
                    oversubscribe=oversubscribe,
                    init_function=init_function,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
            else:
                return PySlurmStepExecutor(
                    max_cores=max_cores,
                    cores_per_worker=cores_per_worker,
                    threads_per_core=threads_per_core,
                    gpus_per_worker=gpus_per_worker,
                    oversubscribe=oversubscribe,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
        else:  # backend="mpi"
            if threads_per_core != 1:
                raise ValueError(
                    "Thread based parallelism is not supported for the pympipool.mpi.PyMPIExecutor backend."
                    "Please use threads_per_core=1 instead of threads_per_core="
                    + str(threads_per_core)
                    + "."
                )
            if gpus_per_worker != 0:
                raise ValueError(
                    "GPU assignment is not supported for the pympipool.mpi.PyMPIExecutor backend."
                    "Please use gpus_per_worker=0 instead of gpus_per_worker="
                    + str(gpus_per_worker)
                    + "."
                )
            if block_allocation:
                return PyMPIExecutor(
                    max_workers=int(max_cores / cores_per_worker),
                    cores_per_worker=cores_per_worker,
                    init_function=init_function,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
            else:
                return PyMPIStepExecutor(
                    max_cores=max_cores,
                    cores_per_worker=cores_per_worker,
                    cwd=cwd,
                    hostname_localhost=hostname_localhost,
                )
