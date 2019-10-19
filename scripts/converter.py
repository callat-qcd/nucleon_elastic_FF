# NOTE from AWL 
# - we need the valence fermion action to have multiple quark masses
# - we need to set the gaugeaction smearing to HISQ or something
# - we need to have the valence action have the FLOW_TIME params
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

# This dictionary specifies which tables we want to use to create a one to all propagator
ONE_TO_ALL_TREE = {
    "fermionaction": "MobiusDW",
    "fermionaction.linksmear": "WilsonFlow",
    "gaugeconfig": "Nf211",
    "gaugeconfig.gaugeaction": "LuescherWeisz",
    "gaugeconfig.light": "Hisq",
    "gaugeconfig.light.linksmear": "WilsonFlow",
    "gaugeconfig.strange": "Hisq",
    "gaugeconfig.strange.linksmear": "WilsonFlow",
    "gaugeconfig.charm": "Hisq",
    "gaugeconfig.charm.linksmear": "WilsonFlow",
    "sourcesmear": "GaugeCovariantGaussian",
    "sinksmear": "Point",
}

CONVERTER = {}
INVERTER  = {}

# Here we need to enter the name of the parameter used in nucleon_elastic_FF

# gagugeconfig
CONVERTER["STREAM"] = "gagugeconfig.stream"  # Stream tag for Monte Carlo
CONVERTER["CFG"] = "gagugeconfig.config"  # Configuration number
CONVERTER["NL"] = "gagugeconfig.nx"  # Spatial length in lattice units
CONVERTER["NL"] = "gagugeconfig.ny"  # Spatial length in lattice units
CONVERTER["NL"] = "gagugeconfig.nz"  # Spatial length in lattice units
CONVERTER["NT"] = "gagugeconfig.nt"  # Temporal length in lattice units
CONVERTER["ENS_ABBR"] = "gagugeconfig.short_tag"  # (Optional) Short name (e.g. 'a15m310')
def get_a(params):
    a = params["ENS_ABBR"].split('m')[0]
    a = a.split('a')[1]
    return a
def get_mpi(params):
    m = params["ENS_ABBR"].split('m')[1]
    return m

INVERTER["gagugeconfig.mpi"] = get_mpi
INVERTER["gaugeconfig.gaugeaction.a_fm"] = get_a

# gaugeconfig.gaugeaction
def get_beta(params):
    b = params["ENS_LONG"].split('b')[1].split('m')[0]
    beta = b[0]+'.'+b[1:]
    return beta
INVERTER["gaugeconfig.gaugeaction.beta"] = get_beta
#CONVERTER["BETA"] = "gaugeconfig.gaugeaction.beta"  # Coupling constant
CONVERTER["U0"] = "gaugeconfig.gaugeaction.u0"  # Tadpole improvement coefficient


# gaugeconfig.light
INVERTER["gaugeconfig.light.quark_tag"] = lambda params: "light"
CONVERTER["MS_L"] = "gaugeconfig.light.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.light.naik"] = lambda params: 0.

# gaugeconfig.light.linksmear
INVERTER["flowtime"] = lambda params: params["FLOW_TIME"]
INVERTER["flowstep"] = lambda params: params["FLOW_STEP"]


# gaugeconfig.strange
INVERTER["gaugeconfig.strange.quark_tag"] = lambda params: "strange"
CONVERTER["MS_S"] = "gaugeconfig.strange.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.strange.naik"] = lambda params: 0.

# gaugeconfig.charm
INVERTER["gaugeconfig.charm.quark_tag"] = lambda params: "charm"
CONVERTER["MS_C"] = "gaugeconfig.charm.quark_mass"  # Input quark mass
INVERTER["gaugeconfig.charm.naik"] = lambda params: params["NAIK"]

# fermionaction
CONVERTER[""] = "fermionaction.quark_mass"  # Input quark mass
CONVERTER[""] = "fermionaction.quark_tag"  # Type of quark
CONVERTER["L5"] = "fermionaction.l5"  # Length of 5th dimension
CONVERTER["M5"] = "fermionaction.m5"  # 5th dimensional mass
CONVERTER["B5"] = "fermionaction.b5"  # Mobius kernel parameter [a5 = b5 - c5, alpha5 * a5…
CONVERTER["C5"] = "fermionaction.c5"  # Mobius kernal perameter

# fermionaction.linksmear
CONVERTER[""] = "fermionaction.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "fermionaction.linksmear.flowstep"  # Number of diffusion steps


# sourcesmear
CONVERTER[""] = "radius"  # Smearing radius in lattice units
CONVERTER[""] = "step"  # Number of smearing steps


# propagator OneToAll
CONVERTER["x"] = "origin_x"  # x-coordinate origin location of the propagator
CONVERTER["y"] = "origin_y"  # y-coordinate origin location of the propagator
CONVERTER["z"] = "origin_z"  # z-coordinate origin location of the propagator
CONVERTER["t"] = "origin_t"  # t-coordinate origin location of the propagator
