"""Dictionary which maps nucleon_elastic_FF parameters to lattedb parameters

We are going to create a
`OneToAll` propagator with a
-> `MobiusDW` fermion action
-> `Nf211` gauge configs
    -> Based on `Hisq` actions
    -> With a `LuescherWeisz` gagugeaction
    -> `WilsonFlow` ed gaugesmear
"""

# This dictionary specifies which tables we want to use to create a one to all propagator
## see also https://ithems.lbl.gov/lattedb/documentation/propagator/#onetoall
## or
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
# If keys are the same for all database objects, we do not have to specify them each time

# gagugeconfig
CONVERTER[""] = "gagugeconfig.stream"  # Stream tag for Monte Carlo
CONVERTER[""] = "gagugeconfig.config"  # Configuration number
CONVERTER[""] = "gagugeconfig.nx"  # Spatial length in lattice units
CONVERTER[""] = "gagugeconfig.ny"  # Spatial length in lattice units
CONVERTER[""] = "gagugeconfig.nz"  # Spatial length in lattice units
CONVERTER[""] = "gagugeconfig.nt"  # Temporal length in lattice units
CONVERTER[""] = "gagugeconfig.short_tag"  # (Optional) Short name (e.g. 'a15m310')
CONVERTER[""] = "gagugeconfig.mpi"  # (Optional) Pion mass in MeV


# gaugeconfig.gaugeaction
CONVERTER[""] = "gaugeconfig.gaugeaction.beta"  # Coupling constant
CONVERTER[""] = "gaugeconfig.gaugeaction.a_fm"  # Lattice spacing in fermi
CONVERTER[""] = "gaugeconfig.gaugeaction.u0"  # Tadpole improvement coefficient


# gaugeconfig.light
CONVERTER[""] = "gaugeconfig.light.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.light.quark_tag"  # Type of quark
CONVERTER[""] = "gaugeconfig.light.naik"  # Coefficient of Naik term.

# gaugeconfig.light.linksmear
CONVERTER[""] = "gaugeconfig.light.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "gaugeconfig.light.linksmear.flowstep"  # Number of diffusion steps


# gaugeconfig.strange
CONVERTER[""] = "gaugeconfig.strange.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.strange.quark_tag"  # Type of quark
CONVERTER[""] = "gaugeconfig.strange.naik"  # Coefficient of Naik term.

# gaugeconfig.strange.linksmear
CONVERTER[""] = "gaugeconfig.strange.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "gaugeconfig.strange.linksmear.flowstep"  # Number of diffusion steps


# gaugeconfig.charm
CONVERTER[""] = "gaugeconfig.charm.quark_mass"  # Input quark mass
CONVERTER[""] = "gaugeconfig.charm.quark_tag"  # Type of quark
CONVERTER[""] = "gaugeconfig.charm.naik"  # Coefficient of Naik term.

# gaugeconfig.charm.linksmear
CONVERTER[""] = "gaugeconfig.charm.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "gaugeconfig.charm.linksmear.flowstep"  # Number of diffusion steps


# fermionaction
CONVERTER[""] = "fermionaction.quark_mass"  # Input quark mass
CONVERTER[""] = "fermionaction.quark_tag"  # Type of quark
CONVERTER[""] = "fermionaction.l5"  # Length of 5th dimension
CONVERTER[""] = "fermionaction.m5"  # 5th dimensional mass
CONVERTER[""] = "fermionaction.b5"  # Mobius kernel parameter [a5 = b5 - c5, alpha5 * a5…
CONVERTER[""] = "fermionaction.c5"  # Mobius kernal perameter

# fermionaction.linksmear
CONVERTER[""] = "fermionaction.linksmear.flowtime"  # Flow time in lattice units
CONVERTER[""] = "fermionaction.linksmear.flowstep"  # Number of diffusion steps


# sourcesmear
CONVERTER[""] = "radius"  # Smearing radius in lattice units
CONVERTER[""] = "step"  # Number of smearing steps


# propagator OneToAll
CONVERTER[""] = "origin_x"  # x-coordinate origin location of the propagator
CONVERTER[""] = "origin_y"  # y-coordinate origin location of the propagator
CONVERTER[""] = "origin_z"  # z-coordinate origin location of the propagator
CONVERTER[""] = "origin_t"  # t-coordinate origin location of the propagator
