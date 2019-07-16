from __future__ import print_function
import os, sys, argparse, shutil, datetime, time
import numpy as np

np.set_printoptions(linewidth=180)
import tables as h5
import warnings

warnings.simplefilter("ignore", h5.NaturalNameWarning)
from glob import glob

"""
    NUCLEON_ELASTIC_FF IMPORTS
"""
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), "area51_files"))
import importlib
import c51_mdwf_hisq as c51
import utils
import sources

import re

message = {
    "res_phi": "MRES and PHI_QQ",
    "spec": "PIONS and PROTONS",
    "formfac": "PROTON FORMFAC",
}

from lattedb.correlator.models import DWFTuning


def get_data(params, d_type):
    # switch for data types to define h5 path
    if d_type == "res_phi":
        prop_name = c51.names["prop"] % params


def put_data(params, d_type, data=None, overwrite=False, db_info=False):
    # switch for data types to define h5 path
    if d_type == "res_phi":
        # data file
        data_file = (
            params["data_dir"]
            + "/"
            + params["ens_s"]
            + "_"
            + params["CFG"]
            + "_srcs"
            + params["src_ext"]
            + ".h5"
        )
        # define h5 directories
        mp_dir = (
            "/"
            + params["val_p"]
            + "/dwf_jmu/mq"
            + params["MQ"].replace(".", "p")
            + "/midpoint_pseudo"
        )
        pp_dir = (
            "/"
            + params["val_p"]
            + "/dwf_jmu/mq"
            + params["MQ"].replace(".", "p")
            + "/pseudo_pseudo"
        )
        phi_dir = "/" + params["val_p"] + "/phi_qq/mq" + params["MQ"].replace(".", "p")
        # if db_info, just print information
        if db_info:
            for corr in [mp_dir, pp_dir]:
                print("data key  : mres")
                print("data file : %s" % data_file)
                print("h5 path   : %s" % (corr + "/" + params["SRC"]))

            parameters = translate(params)
            tree = {
                "propagator": (
                    "MobiusDWF",
                    {"gaugeconfig": "Hisq", "gaugesmear": "WilsonFlow"},
                ),
                "source": ("Meson", {"hadronsmear": "Gaussian"}),
            }

            DWFTuning.get_or_create_from_parameters(
                parameters=parameters, tree=tree, dry_run=False
            )

        else:
            print("putting data not supported yet")


def translate(params):
    HBARC = 197

    print(params)

    beta_to_afm = {"5.8": "0.15", "6": "1.2", "6.3": "0.09", "6.72": "0.06"}
    a_fm = beta_to_afm[params["BETA"]]

    l_fm = int(params["NL"]) * float(a_fm)

    pattern = r"a(P<a>:[0-9]+)m(P<mpi>:[0-9]+)"
    match = re.search(pattern, params["ENS_ABBR"])
    mpi = int(match.groupdict()["mpi"]) if match else None

    nconfig = (params["cfg_f"] - params["cfg_i"]) / params["cfg_d"]
    if abs(int(nconfig) - nconfig) > 1.0e-12:
        raise ValueError("Float number of configs:  %f ?!" % nconfig)
    else:
        nconfig = int(nconfig)

    ml_string = params["MS_L"].split(".")[-1]
    ms_string = params["MS_S"].split(".")[-1]
    mc_string = params["MS_C"].split(".")[-1]
    tag = (
        "l{NL}{NT}f{dlq}{sq}{cq}b{BETA:1.2f}"
        "m{ml_string}m{ms_string}m{mc_string}{STREAM}"
    ).format(
        dlq=2,
        sq=1,
        cq=1,
        ml_string=ml_string,
        ms_string=ms_string,
        mc_string=mc_string,
        NL=params["NL"],
        NT=params["NT"],
        BETA=float(params["BETA"]),
        STREAM=params["STREAM"],
    )

    parameters = dict(
        a_fm=a_fm,
        beta=params["BETA"],
        l_fm=l_fm,
        ml=params["MS_L"],
        ms=params["MS_S"],
        mc=params["MS_C"],
        mpi=mpi,
        mpil=mpi * l_fm / HBARC if mpi is not None else None,
        naik=params["NAIK"],
        nconfig=nconfig,
        nt=params["NT"],
        nx=params["NL"],
        short_tag=params["ENS_ABBR"],
        stream=params["STREAM"],
        u0=params["U0"],
    )

    tag = "gf{gf}_n{fs}".format(
        gf=params["FLOW_TIME"].replace(".", "p"), fs=params["FLOW_STEP"]
    )
    parameters.update(dict(flowtime=params["FLOW_TIME"], flowstep=params["FLOW_STEP"]))

    a5 = 1.0

    origin = re.search(
        "x(?P<x>[0-9]+)y(?P<y>[0-9]+)z(?P<z>[0-9]+)t(?P<t>[0-9]+)", params["SRC"]
    )

    parameters.update(
        dict(
            a5=a5,
            alpha5=params["alpha5"],
            b5=params["B5"],
            c5=params["C5"],
            l5=params["L5"],
            m5=params["M5"],
            mval=params["MV_L"],
            origin_x=origin["x"],
            origin_y=origin["y"],
            origin_z=origin["z"],
            origin_t=origin["t"],
        )
    )

    parameters["isospin_x2"] = 1
    parameters["isospin_z_x2"] = 1
    parameters["parity"] = 1
    parameters["spin_x2"] = 1
    parameters["spin_z_x2"] = 1
    parameters["strangeness"] = 1
    parameters["structure"] = r"$\gamma_5$"

    parameters["radius"] = 1
    parameters["step"] = 1

    parameters["sink5"] = True

    print(parameters)

    return parameters


def main():
    fmt = "%Y-%m-%d %H:%M:%S"

    ens, stream = c51.ens_base()
    ens_s = ens + "_" + stream

    print(ens)
    area51 = importlib.import_module(ens)
    PARAMS = area51.params
    PARAMS["ens_s"] = ens_s

    PARAMS["machine"] = c51.machine
    PARAMS["ENS_LONG"] = c51.ens_long[ens]
    PARAMS["ENS_S"] = ens_s
    PARAMS["STREAM"] = stream

    print("ENSEMBLE:", ens_s)

    """
        COMMAND LINE ARG PARSER
    """
    parser = argparse.ArgumentParser(description="get data and put in h5 files")
    parser.add_argument("data_type", type=str, help="[res_phi spec formfac]")
    parser.add_argument("--cfgs", nargs="+", type=int, help="cfgs: ci [cf dc]")
    parser.add_argument("-s", "--src", type=str, help="src [xXyYzZtT] None=All")
    parser.add_argument(
        "-o",
        default=False,
        action="store_const",
        const=True,
        help="overwrite? [%(default)s]",
    )
    parser.add_argument(
        "--move",
        default=False,
        action="store_const",
        const=True,
        help="move bad files? [%(default)s]",
    )
    parser.add_argument(
        "-v",
        default=True,
        action="store_const",
        const=False,
        help="verbose? [%(default)s]",
    )
    parser.add_argument(
        "-d",
        "--db_info",
        default=False,
        action="store_const",
        const=True,
        help="print DB info and not collect? [%(default)s]",
    )
    args = parser.parse_args()
    print("Arguments passed")
    print(args)
    print("")

    dtype = np.float64
    # make sure the h5 data directory exists
    data_dir = c51.data_dir % PARAMS
    utils.ensure_dirExists(data_dir)
    PARAMS["data_dir"] = data_dir

    # if we read si, sf, ds from area51 file, user is over-riding default
    if "si" in PARAMS and "sf" in PARAMS and "ds" in PARAMS:
        tmp_PARAMS = dict()
        tmp_PARAMS["si"] = PARAMS["si"]
        tmp_PARAMS["sf"] = PARAMS["sf"]
        tmp_PARAMS["ds"] = PARAMS["ds"]
        PARAMS = sources.src_start_stop(PARAMS, ens, stream)
        PARAMS["si"] = tmp_PARAMS["si"]
        PARAMS["sf"] = tmp_PARAMS["sf"]
        PARAMS["ds"] = tmp_PARAMS["ds"]
    else:
        PARAMS = sources.src_start_stop(PARAMS, ens, stream)

    # Get cfg and src list, create source extension for name
    cfgs_run, srcs = utils.parse_cfg_src_argument(args.cfgs, args.src, PARAMS)
    src_ext = "%d-%d" % (PARAMS["si"], PARAMS["sf"])
    PARAMS["src_ext"] = src_ext

    # get the valence information
    smr = "gf" + PARAMS["FLOW_TIME"] + "_w" + PARAMS["WF_S"] + "_n" + PARAMS["WF_N"]
    val = smr + "_M5" + PARAMS["M5"] + "_L5" + PARAMS["L5"] + "_a" + PARAMS["alpha5"]
    val_p = val.replace(".", "p")
    PARAMS["val"] = val
    PARAMS["val_p"] = val_p

    # for now, we are ONLY doing the light quark
    mv_l = PARAMS["MV_L"]
    PARAMS["MQ"] = PARAMS["MV_L"]

    print("MINING %s" % (message[args.data_type]))
    print("ens_stream = %s" % (ens_s))
    if len(cfgs_run) == 1:
        dc = 1
    else:
        dc = cfgs_run[1] - cfgs_run[0]
    print("cfgs_i : cfg_f : dc = %d : %d : %d" % (cfgs_run[0], cfgs_run[-1], dc))
    print(
        "si - sf x ds        = %d - %d x %d\n"
        % (PARAMS["si"], PARAMS["sf"], PARAMS["ds"])
    )
    time.sleep(2)

    # if db_info, we are just printing the h5 file path, h5 dir info and key
    tmp_parmas = PARAMS.copy()
    if args.db_info:
        print("printing info for the database")
        for cfg in cfgs_run:
            no = str(cfg)
            tmp_parmas["CFG"] = no
            tmp_parmas = c51.ensemble(tmp_parmas)
            for src in srcs[cfg]:
                tmp_parmas["SRC"] = src
                put_data(
                    params=tmp_parmas,
                    d_type=args.data_type,
                    overwrite=args.o,
                    db_info=args.db_info,
                )

    # else, collect data and put it in the h5 files
    else:
        print("collecting data")
        for cfg in cfgs_run:
            no = str(cfg)
            sys.stdout.write("  cfg=%4d\r" % (cfg))
            sys.stdout.flush()


if __name__ == "__main__":
    main()
