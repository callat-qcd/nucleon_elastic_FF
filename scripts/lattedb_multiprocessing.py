"""Example script to run several db queris at once on multiple processes.

See also:
* Multiprocessing in python: https://docs.python.org/3/library/multiprocessing.html
* Django multiprocessing and DB connections: https://stackoverflow.com/a/10684672
"""
from typing import Dict, List, Any
from multiprocessing import Process
import os
from time import sleep

from numpy import split, array

# from django import db

# import lattedb_ff_disk_tape_functions as lattedb_ff

# import c51_mdwf_hisq as c51


class Worker:
    """Implements storage class for running multiple process.

    Assumes looping over cfgs is valid.
    """

    def __init__(
        self,
        name
        # params: Dict[str, Any], srcs, src_set, stream, ens, meta_entries, f_type
    ):
        """Init work with meta parameters."""
        self.name = name
        # self.params = params
        # self.srcs = srcs
        # self.src_set = src_set
        # self.stream = stream
        # self.ens = ens
        # self.meta_entries = meta_entries
        # self.f_type = f_type

    def run(self, cfgs: List[int]):
        """Runjob for a given set of cfgs."""

        print(self.name)
        print("module name:", __name__)
        print("parent process:", os.getppid())
        print("process id:", os.getpid())

        sleep(1)
        print("process id:", os.getpid(), "done")

        # Code which should be used in detail
        return
        params = self.params.copy()
        for cfg in cfgs:
            no = str(cfg)
            params["CFG"] = no
            params = c51.ensemble(params)
            params["SOURCES"] = self.srcs[cfg]
            if self.f_type in ["spec_4D_tslice_avg", "all"]:
                lattedb_ff.collect_spec_ff_4D_tslice_src_avg(
                    "spec", params, self.meta_entries["spec_4D_tslice_avg"]
                )

            if self.f_type in ["formfac_4D_tslice_src_avg", "all"]:
                for dt in params["t_seps"]:
                    params["T_SEP"] = str(dt)
                    lattedb_ff.collect_spec_ff_4D_tslice_src_avg(
                        "formfac",
                        params,
                        self.meta_entries["formfac_4D_tslice_src_avg"],
                    )


def main():
    """Launch several proccess which exectute worker.run."""
    # Do stuff here to setup worker
    worker = Worker(name="worker")
    n_processes = 8
    cfgs = list(range(16))

    processes = []
    # Ensure each process re-connects to DB with own id
    # The below line needs to commented out once the db is corretly configured
    # db.connections.close_all()

    # Launch individual processes
    for cfg_subset in split(array(cfgs), n_processes):
        process = Process(target=worker.run, args=(cfg_subset,))
        processes.append(process)
        process.start()

    # Complete processes
    for process in processes:
        process.join()


if __name__ == "__main__":
    main()
