"""Dictionary which maps nucleon_elastic_FF parameters to lattedb parameters

We are going to create a `OneToAll` propagator.

The idea is to take the `params` dictionary from then `nucleon_elastic_FF` repo
(e.g., `c51_mdwf_hisq.py`) and map keys present in this dictionary to `lattedb` keys.

I have created the values for all the keys needed to create a `OneToAll` table row.

I am not sure yet if this order `nucleon_elastic_FF` -> `lattedb` is the right way.
E.g., we could also try create the mapping from `lattedb` -> `nucleon_elastic_FF`.

What I would like to ask you is:
(1) Does this specification make sense (e.g. do we have the right smearing)?
(2) Could you help me complete this mapping and fill out the missing keys?
    Let me know if you have any questions.
(3) If we would fill all the present entries, is this sufficient to uniquely define a
    `OneToAll` propagator as a physics object? If not, what entries are missing?
(4) What entries are missing to describe files on summit which cannot be computed from
    those parameters?

See also https://ithems.lbl.gov/lattedb/documentation/propagator/#onetoall for table
infos.
Or https://ithems.lbl.gov/lattedb/populate/ to create an actual run script.
"""
from typing import Dict, Any

# This dictionary specifies which tables we want to use to create a one to all propagator
ONE_TO_ALL_TREE = {
    "fermionaction": "MobiusDW",
    "fermionaction.linksmear": "WilsonFlow",
    "gaugeconfig": "Nf211",
    "gaugeconfig.gaugeaction": "LuescherWeisz",
    "gaugeconfig.light": "Hisq",
    "gaugeconfig.light.linksmear": "Unsmeared",
    "gaugeconfig.strange": "Hisq",
    "gaugeconfig.strange.linksmear": "Unsmeared",
    "gaugeconfig.charm": "Hisq",
    "gaugeconfig.charm.linksmear": "Unsmeared",
    "sourcesmear": "GaugeCovariantGaussian",
    "sinksmear": "Point",
}

CONVERTER = {}
INVERTER = {}

# Here we need to enter the name of the parameter used in nucleon_elastic_FF

# gaugeconfig
CONVERTER["STREAM"] = "gaugeconfig.stream"  # Stream tag for Monte Carlo
CONVERTER["CFG"] = "gaugeconfig.config"  # Configuration number
INVERTER["gaugeconfig.nx"] = lambda params: params["NL"]
INVERTER["gaugeconfig.ny"] = lambda params: params["NL"]
INVERTER["gaugeconfig.nz"] = lambda params: params["NL"]
CONVERTER["NT"] = "gaugeconfig.nt"  # Temporal length in lattice units
CONVERTER[
    "ENS_ABBR"
] = "gaugeconfig.short_tag"  # (Optional) Short name (e.g. 'a15m310')

def get_a(params):
    a = params["ENS_ABBR"].split("m")[0]
    a = a.split("a")[1]
    a = "0.%s" %(str(a))
    return a

def get_mpi(params):
    m = params["ENS_ABBR"].split("m")[1]
    return m


INVERTER["gaugeconfig.mpi"] = get_mpi
INVERTER["gaugeconfig.gaugeaction.a_fm"] = get_a

# gaugeconfig.gaugeaction
def get_beta(params):
    b = params["ENS_LONG"].split("b")[1].split("m")[0]
    beta = b[0] + "." + b[1:]
    return beta

INVERTER["gaugeconfig.gaugeaction.beta"] = get_beta
# CONVERTER["BETA"] = "gaugeconfig.gaugeaction.beta"  # Coupling constant
CONVERTER["U0"] = "gaugeconfig.gaugeaction.u0"  # Tadpole improvement coefficient


# gaugeconfig.light
INVERTER["gaugeconfig.light.quark_tag"] = lambda params: "light"
CONVERTER["MS_L"] = "gaugeconfig.light.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.light.naik"] = lambda params: 0.0

# gaugeconfig.strange
INVERTER["gaugeconfig.strange.quark_tag"] = lambda params: "strange"
CONVERTER["MS_S"] = "gaugeconfig.strange.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.strange.naik"] = lambda params: 0.0

# gaugeconfig.charm
INVERTER["gaugeconfig.charm.quark_tag"] = lambda params: "charm"
CONVERTER["MS_C"] = "gaugeconfig.charm.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.charm.naik"] = lambda params: params["NAIK"]

# fermionaction
CONVERTER["MV_L"] = "fermionaction.quark_mass"  # Input quark mass
INVERTER["fermionaction.quark_tag"] = lambda params: "light"
CONVERTER["L5"] = "fermionaction.l5"  # Length of 5th dimension
CONVERTER["M5"] = "fermionaction.m5"  # 5th dimensional mass
CONVERTER["B5"] = "fermionaction.b5"  # Mobius kernel parameter [a5 = b5 - c5, alpha5 * a5…
CONVERTER["C5"] = "fermionaction.c5"  # Mobius kernal perameter

# fermionaction.linksmear
INVERTER["fermionaction.linksmear.flowtime"] = lambda params: params["FLOW_TIME"]
INVERTER["fermionaction.linksmear.flowstep"] = lambda params: params["FLOW_STEP"]

# sourcesmear
CONVERTER["WF_S"] = "radius"  # Smearing radius in lattice units
CONVERTER["WF_N"] = "step"  # Number of smearing steps


# propagator OneToAll
CONVERTER["X0"] = "origin_x"  # x-coordinate origin location of the propagator
CONVERTER["Y0"] = "origin_y"  # y-coordinate origin location of the propagator
CONVERTER["Z0"] = "origin_z"  # z-coordinate origin location of the propagator
CONVERTER["T0"] = "origin_t"  # t-coordinate origin location of the propagator


def get_lattedb_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Uses the converter and inverter dictionaries to map nucleon_elastic_FF keys
    to lattedb keys.
    """
    lattedb_params = {}

    for nuc_key, lattedb_key in CONVERTER.items():
        lattedb_params[lattedb_key] = params[nuc_key]

    for lattedb_key, mapping in INVERTER.items():
        lattedb_params[lattedb_key] = mapping(params)

    return lattedb_params


def get_or_create_one_to_all(lattedb_params: Dict[str, Any]) -> "OneToAll":
    """Creates a OneToAll propagator for input parameters
    """
    from lattedb.propagator.models import OneToAll

    propagator, created = OneToAll.get_or_create_from_parameters(
        lattedb_params, tree=ONE_TO_ALL_TREE
    )

    if created:
        print(f"Propagator entry {propagator} was created")

    return propagator
