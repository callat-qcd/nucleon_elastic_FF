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

# Here we need to enter the name of the parameter used in nucleon_elastic_FF

# gagugeconfig
CONVERTER[""] = "gagugeconfig.stream"  # Stream tag for Monte Carlo
CONVERTER["CFG"] = "gagugeconfig.config"  # Configuration number
CONVERTER["NL"] = "gagugeconfig.nx"  # Spatial length in lattice units
CONVERTER["NL"] = "gagugeconfig.ny"  # Spatial length in lattice units
CONVERTER["NL"] = "gagugeconfig.nz"  # Spatial length in lattice units
CONVERTER["NT"] = "gagugeconfig.nt"  # Temporal length in lattice units
CONVERTER["ENS_ABBR"] = "gagugeconfig.short_tag"  # (Optional) Short name (e.g. 'a15m310')
CONVERTER[""] = "gagugeconfig.mpi"  # (Optional) Pion mass in MeV


# gaugeconfig.gaugeaction
CONVERTER["BETA"] = "gaugeconfig.gaugeaction.beta"  # Coupling constant
CONVERTER[""] = "gaugeconfig.gaugeaction.a_fm"  # Lattice spacing in fermi
CONVERTER["U0"] = "gaugeconfig.gaugeaction.u0"  # Tadpole improvement coefficient


# gaugeconfig.light
CONVERTER[""] = "gaugeconfig.light.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.light.quark_tag"  # Type of quark
CONVERTER["NAIK"] = "gaugeconfig.light.naik"  # Coefficient of Naik term.

# gaugeconfig.light.linksmear
CONVERTER["FLOW_TIME"] = "gaugeconfig.light.linksmear.flowtime"  # Flow time in lattice units
CONVERTER["FLOW_STEP"] = "gaugeconfig.light.linksmear.flowstep"  # Number of diffusion steps


# gaugeconfig.strange
CONVERTER[""] = "gaugeconfig.strange.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.strange.quark_tag"  # Type of quark
CONVERTER["NAIK"] = "gaugeconfig.strange.naik"  # Coefficient of Naik term.

# gaugeconfig.strange.linksmear
CONVERTER[""] = "gaugeconfig.strange.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "gaugeconfig.strange.linksmear.flowstep"  # Number of diffusion steps


# gaugeconfig.charm
CONVERTER[""] = "gaugeconfig.charm.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.charm.quark_tag"  # Type of quark
CONVERTER["NAIK"] = "gaugeconfig.charm.naik"  # Coefficient of Naik term.

# gaugeconfig.charm.linksmear
CONVERTER[""] = "gaugeconfig.charm.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "gaugeconfig.charm.linksmear.flowstep"  # Number of diffusion steps


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
