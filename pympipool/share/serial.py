import inspect
import os
import socket
import queue

import cloudpickle

from pympipool.share.communication import SocketInterface


def command_line_options(
    hostname,
    port_selected,
    path,
    cores,
    cores_per_task=1,
    oversubscribe=False,
    enable_flux_backend=False,
    enable_mpi4py_backend=True,
):
    if enable_flux_backend:
        command_lst = ["flux", "run"]
    else:
        command_lst = ["mpiexec"]
    if oversubscribe:
        command_lst += ["--oversubscribe"]
    if cores_per_task == 1 and enable_mpi4py_backend:
        command_lst += ["-n", str(cores), "python", "-m", "mpi4py.futures"]
    elif cores_per_task > 1 and enable_mpi4py_backend:
        # Running MPI parallel tasks within the map() requires mpi4py to use mpi spawn:
        # https://github.com/mpi4py/mpi4py/issues/324
        command_lst += ["-n", "1", "python"]
    else:
        command_lst += ["-n", str(cores), "python"]
    command_lst += [path]
    if enable_flux_backend:
        command_lst += [
            "--host",
            hostname,
        ]
    command_lst += [
        "--zmqport",
        str(port_selected),
    ]
    if enable_mpi4py_backend:
        command_lst += [
            "--cores-per-task",
            str(cores_per_task),
            "--cores-total",
            str(cores),
        ]
    return command_lst


def get_parallel_subprocess_command(
    port_selected,
    cores,
    cores_per_task,
    oversubscribe,
    enable_flux_backend,
    enable_mpi4py_backend,
):
    if enable_mpi4py_backend:
        executable = "mpipool.py"
    else:
        executable = "mpiexec.py"
    command_lst = command_line_options(
        hostname=socket.gethostname(),
        port_selected=port_selected,
        path=os.path.abspath(os.path.join(__file__, "../../executor", executable)),
        cores=cores,
        cores_per_task=cores_per_task,
        oversubscribe=oversubscribe,
        enable_flux_backend=enable_flux_backend,
        enable_mpi4py_backend=enable_mpi4py_backend,
    )
    return command_lst


def execute_tasks(future_queue, cores, oversubscribe, enable_flux_backend, cwd=None):
    interface = SocketInterface()
    interface.bootup(
        command_lst=get_parallel_subprocess_command(
            port_selected=interface.bind_to_random_port(),
            cores=cores,
            cores_per_task=1,
            oversubscribe=oversubscribe,
            enable_flux_backend=enable_flux_backend,
            enable_mpi4py_backend=False,
        ),
        cwd=cwd,
    )
    while True:
        task_dict = future_queue.get()
        if "c" in task_dict.keys() and task_dict["c"] == "close":
            interface.shutdown(wait=True)
            break
        elif "f" in task_dict.keys() and "l" in task_dict.keys():
            f = task_dict.pop("l")
            if f.set_running_or_notify_cancel():
                f.set_result(interface.send_and_receive_dict(input_dict=task_dict))
        elif "f" in task_dict.keys() and "i" in task_dict.keys():
            interface.send_dict(input_dict=task_dict)


def _cloudpickle_update(ind=2):
    # Cloudpickle can either pickle by value or pickle by reference. The functions which are communicated have to
    # be pickled by value rather than by reference, so the module which calls the map function is pickled by value.
    # https://github.com/cloudpipe/cloudpickle#overriding-pickles-serialization-mechanism-for-importable-constructs
    # inspect can help to find the module which is calling pympipool
    # https://docs.python.org/3/library/inspect.html
    # to learn more about inspect another good read is:
    # http://pymotw.com/2/inspect/index.html#module-inspect
    # 1 refers to 1 level higher than the map function
    try:  # When executed in a jupyter notebook this can cause a ValueError - in this case we just ignore it.
        cloudpickle.register_pickle_by_value(inspect.getmodule(inspect.stack()[ind][0]))
    except ValueError:
        pass


def cancel_items_in_queue(que):
    while True:
        try:
            item = que.get_nowait()
            if isinstance(item, dict) and "l" in item.keys():
                item["l"].cancel()
        except queue.Empty:
            break