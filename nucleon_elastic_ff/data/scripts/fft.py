"""Script for time fourier transforming correlator data
"""
from typing import Optional
from typing import List

import os

import h5py
import numpy as np

from nucleon_elastic_ff.utilities import set_up_logger
from nucleon_elastic_ff.utilities import find_all_files
from nucleon_elastic_ff.utilities import has_match

from nucleon_elastic_ff.data.h5io import get_dsets
from nucleon_elastic_ff.data.h5io import create_dset
from nucleon_elastic_ff.data.h5io import get_dset_chunks

from nucleon_elastic_ff.data.arraymanip import get_fft

LOGGER = set_up_logger("nucleon_elastic_ff")


def fft(  # pylint: disable = R0913
    root: str,
    name_input: str,
    name_output: str,
    max_momentum: Optional[int] = None,
    chunk_size: Optional[int] = None,
    overwrite: bool = False,
    cuda: bool = True,
):
    """Recursively scans dir for files, ffts and shifts and chops user specified momenta.

    Routine FFTs 4D correlation functions. If `max_momentum` is given this routine cuts
    the output array in a all momentum directions.

    .. note::
        The user specifies ``max_momentum = 5``, which means, in each direction,
        ``x, y, z``, the momentum should is of from ``[0,1,2,3,4,5,-5,-4,-3,-2,-1]``,
        just like a regular FFT space, except the higher valued modes are chopped out.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.
    Once all files are fixed, this routine calls `slice_file` on each file.
    This routines transforms ``local_current`` dsets to ``momentum_current`` dsets.

    .. Note::
        This routine explicitly assumes that the datasets to transform are of shape
        ``shape1 + [Nz, Ny, Nx] + [2]`` where shape1 can be anything the second shape is
        the to transformed shape and the last shape corresponds to real / complex.

    **Arguments**
        root: str
            The directory to look for files.

        name_input: str
            Files must match this pattern to be submitted for slicing.

        name_output: str
            Files must not match this pattern to be submitted for slicing.
            Also the sliced output files will have the input name replaced by the output
            name. This also includes directory names.

        max_momentum: int
            The momentum at which the FT is cutoff in each spatial dimension.

        chunk_size: Optional[int] = None
            Reads in arrays in chunks and applys fft chunkwise.
            This reduce the memory load.
            For now, only slices the zeroth-dimension.

        overwrite: bool = False
            Overwrite existing sliced files.

        cuda: bool = True
            Use `cupy` to run fft if possible.
    """
    LOGGER.info("Starting FFT of files")
    LOGGER.info("Looking into `%s`", root)
    LOGGER.info(
        "Using naming convention `%s` -> `%s` (for sliced data) ",
        name_input,
        name_output,
    )

    all_files = find_all_files(
        root,
        file_patterns=[name_input + r".*\.h5$"],
        exclude_file_patterns=[name_output],
    )
    if not overwrite:
        all_files = [
            file
            for file in all_files
            if not os.path.exists(file.replace(name_input, name_output))
        ]
    LOGGER.info(
        "Found %d files which match the pattern%s",
        len(all_files),
        " " if overwrite else " (and do not exist)",
    )

    for n_file, file_address in enumerate(all_files):
        LOGGER.info("--- File %d of %d ---", n_file + 1, len(all_files))
        file_address_out = file_address.replace(name_input, name_output)
        if not os.path.exists(os.path.dirname(file_address_out)):
            os.makedirs(os.path.dirname(file_address_out))
        fft_file(
            file_address,
            file_address_out,
            max_momentum=max_momentum,
            chunk_size=chunk_size,
            overwrite=overwrite,
            cuda=cuda,
        )

    LOGGER.info("Done")


def fft_file(  # pylint: disable = R0914, R0913, R0912
    file_address_in: str,
    file_address_out: str,
    max_momentum: Optional[int] = None,
    dset_patterns: List[str] = (
        "local_current",
        "x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+",
        "4D_correlator",
    ),
    chunk_size: Optional[int] = None,
    overwrite: bool = False,
    cuda: bool = True,
):
    """Reads input file and writes ffts and cuts data to output file.

    This methods scans all datasets within the file.
    If a data set has "local_current" in its name it is ffted in its spatial components.
    The slicing info is inferred by the argument `max_momentum`.
    This routines transforms `local_current` dsets to `momentum_current` dsets.
    Also the slicing meta info is stored in the resulting output file in the `meta`
    attribute of `momentum_current`.

    .. note::
        The user specifies ``max_momentum = 5``, which means, in each direction,
        ``x, y, z``, the momentum should is of from ``[0,1,2,3,4,5,-5,-4,-3,-2,-1]``,
        just like a regular FFT space, except the higher valued modes are chopped out.

    .. Note::
        This routine explicitly assumes that the datasets to transform are of shape
        ``shape1 + [Nz, Ny, Nx] + [2]`` where shape1 can be anything the second shape is
        the to transformed shape and the last shape corresponds to real / complex.

    **Arguments**
        file_address_in: str
            Address of the to be scanned and sliced HDF5 file.

        file_address_out: str
            Address of the output HDF5 file.

        max_momentum: Optional[int] = None
            The momentum at which the FT is cutoff in each spatial dimension.

        dset_patterns: List[str] = (
            "local_current",
            "x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+",
            "4D_correlator",
        ),
            List of regex patterns data sets must match to be ffted (needs to match one).

        chunk_size: Optional[int] = None
            Reads in arrays in chunks and applys fft chunkwise.
            This reduce the memory load.
            For now, only slices the zeroth-dimension.

        overwrite: bool = False
            Overwrite existing sliced file.

        cuda: bool = True
            Use `cupy` to run fft if possible.

    **Raises**
        KeyError:
            If no dset was transformed.
    """
    LOGGER.info("Sclicing\n\t  `%s`\n\t->`%s`", file_address_in, file_address_out)

    transformed_dstes = 0

    with h5py.File(file_address_in, "r") as h5f:
        dsets = get_dsets(h5f, load_dsets=False)

        LOGGER.info("Start fft for %d dsets", len(dsets))
        with h5py.File(file_address_out) as h5f_out:
            for name, dset in dsets.items():

                if has_match(name, dset_patterns, match_all=False):
                    if "local_current" in name:
                        name = name.replace("local_current", "momentum_current")
                    LOGGER.debug("Start fft procedure for dset `%s`", name)
                    shape = dset.shape

                    if shape[-1] != 2:
                        raise ValueError(
                            f"Expected last shape entry of dset `{name}` to be 2 but"
                            f" received {shape[1]}"
                        )
                    if len(shape) < 4:
                        raise ValueError(
                            f"Expected dset `{name}` to have at least 4 dimensions but"
                            f" only found {len(shape)}"
                        )
                    if not shape[-2] == shape[-3] == shape[-4]:
                        raise ValueError(
                            f"Expected dset `{name}` to have same dimensions in x, y, z"
                            f" but found {shape}"
                        )
                    n1d = shape[-2]

                    LOGGER.debug("\tAdding imag part to real part (removing last dim)")
                    if chunk_size is None:
                        arr = dset[()]
                        arr = (arr.T[0] + arr.T[1] * 1j).T

                        LOGGER.debug("\tStart fft")
                        out = get_fft(arr, cuda=cuda, axes=(-1, -2, -3))
                    else:
                        out = []
                        for n_chunk, chunk in enumerate(
                            get_dset_chunks(dset, chunk_size)
                        ):
                            chunk = (chunk.T[0] + chunk.T[1] * 1j).T
                            LOGGER.debug("\tStart fft of %d. chunk", n_chunk)
                            out.append(get_fft(chunk, cuda=cuda, axes=(-1, -2, -3)))
                        out = np.concatenate(out, axis=0)

                    if max_momentum is not None:
                        meta = dset.attrs.get("meta", None)
                        meta = str(meta) + "&" if meta else ""
                        meta += f"max_momentum=={max_momentum}&n1d_prev=={n1d}"

                        LOGGER.debug("\tSlicing fft")
                        slice_index = list(range(max_momentum + 1))
                        slice_index += [
                            el % n1d
                            for el in range(-max_momentum, 0)  # pylint: disable=E1130
                        ]
                        for axis, key in enumerate(["x", "y", "z"]):
                            axis = -1 * (axis + 1)
                            LOGGER.debug(
                                "\t\t Axis %d: %s -> %s[%s]", axis, key, key, slice_index
                            )
                            out = np.take(out, slice_index, axis=axis)

                    transformed_dstes += 1

                else:
                    meta = None
                    out = dset[()]

                create_dset(h5f_out, name, out, overwrite=overwrite)
                if meta:
                    h5f_out[name].attrs["meta"] = meta

    if transformed_dstes == 0:
        raise KeyError(
            "Could not identify any dsets to parse."
            "Must match one out of `%s`" % dset_patterns
        )


def fft_file_complex_structural_array(  # pylint: disable = R0914, R0913, R0912
    file_address_in: str,
    file_address_out: str,
    max_momentum: Optional[int] = None,
    dset_patterns: List[str] = (
        "local_current",
        "x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+",
        "4D_correlator",
    ),
    chunk_size: Optional[int] = None,
    overwrite: bool = False,
    cuda: bool = True,
):
    """Reads input file and writes ffts and cuts data to output file.

    This methods scans all datasets within the file.
    If a data set has "local_current" in its name it is ffted in its spatial components.
    The slicing info is inferred by the argument `max_momentum`.
    This routines transforms `local_current` dsets to `momentum_current` dsets.
    Also the slicing meta info is stored in the resulting output file in the `meta`
    attribute of `momentum_current`.

    .. note::
        The user specifies ``max_momentum = 5``, which means, in each direction,
        ``x, y, z``, the momentum should is of from ``[0,1,2,3,4,5,-5,-4,-3,-2,-1]``,
        just like a regular FFT space, except the higher valued modes are chopped out.

    .. Note::
        This routine explicitly assumes that the datasets to transform are of shape
        ``shape1 + [Nz, Ny, Nx] + [2]`` where shape1 can be anything the second shape is
        the to transformed shape and the last shape corresponds to real / complex.

    **Arguments**
        file_address_in: str
            Address of the to be scanned and sliced HDF5 file.

        file_address_out: str
            Address of the output HDF5 file.

        max_momentum: Optional[int] = None
            The momentum at which the FT is cutoff in each spatial dimension.

        dset_patterns: List[str] = (
            "local_current",
            "x[0-9]+_y[0-9]+_z[0-9]+_t[0-9]+",
            "4D_correlator",
        ),
            List of regex patterns data sets must match to be ffted (needs to match one).

        chunk_size: Optional[int] = None
            Reads in arrays in chunks and applys fft chunkwise.
            This reduce the memory load.
            For now, only slices the zeroth-dimension.

        overwrite: bool = False
            Overwrite existing sliced file.

        cuda: bool = True
            Use `cupy` to run fft if possible.

    **Raises**
        KeyError:
            If no dset was transformed.
    """
    LOGGER.info("Sclicing\n\t  `%s`\n\t->`%s`", file_address_in, file_address_out)

    transformed_dstes = 0

    with h5py.File(file_address_in, "r") as h5f:
        dsets = get_dsets(h5f, load_dsets=False)

        LOGGER.info("Start fft for %d dsets", len(dsets))
        with h5py.File(file_address_out) as h5f_out:
            for name, dset in dsets.items():

                if has_match(name, dset_patterns, match_all=False):
                    if "local_current" in name:
                        name = name.replace("local_current", "momentum_current")
                    LOGGER.debug("Start fft procedure for dset `%s`", name)
                    shape = dset.shape
                    dt = dset.dtype
                    dtype_shape = tuple()
                    while len(dt.shape) > 0:
                        dtype_shape += dt.shape
                        dt = dt.subdtype[0]
                    dtype_Ndim = len(dtype_shape)

                    if len(shape) < 3:
                        raise ValueError(
                            f"Expected dset `{name}` to have at least 3 dimensions but"
                            f" only found {len(shape)}"
                        )
                    if not shape[-1] == shape[-2] == shape[-3]:
                        raise ValueError(
                            f"Expected dset `{name}` to have same dimensions in x, y, z"
                            f" but found {shape}"
                        )
                    n1d = shape[-1]

                    if chunk_size is None:
                        arr = dset[()]

                        LOGGER.debug("\tStart fft")
                        axes = tuple(-dtype_Ndim-n-1 for n in range(3))
                        out = get_fft(arr, cuda=cuda, axes=axes)
                    else:
                        out = []
                        for n_chunk, chunk in enumerate(
                            get_dset_chunks(dset, chunk_size)
                        ):
                            axes = tuple(-dtype_Ndim-n-1 for n in range(3))
                            LOGGER.debug("\tStart fft of %d. chunk", n_chunk)
                            out.append(get_fft(chunk, cuda=cuda, axes=axes))
                        out = np.concatenate(out, axis=0)

                    meta = dset.attrs.get("meta", None)
                    meta = str(meta) + "&" if meta else ""
                    if max_momentum is not None:
                        meta += f"max_momentum=={max_momentum}&n1d_prev=={n1d}"

                        LOGGER.debug("\tSlicing fft")
                        slice_index = list(range(max_momentum + 1))
                        slice_index += [
                            el % n1d
                            for el in range(-max_momentum, 0)  # pylint: disable=E1130
                        ]
                        for axis, key in enumerate(["x", "y", "z"]):
                            axis = -1 * (axis + 1) -dtype_Ndim
                            LOGGER.debug(
                                "\t\t Axis %d: %s -> %s[%s]", axis, key, key, slice_index
                            )
                            out = np.take(out, slice_index, axis=axis)

                    transformed_dstes += 1

                else:
                    meta = None
                    out = dset[()]

                create_dset(h5f_out, name, out, overwrite=overwrite)
                if meta:
                    h5f_out[name].attrs["meta"] = meta

    if transformed_dstes == 0:
        raise KeyError(
            "Could not identify any dsets to parse."
            "Must match one out of `%s`" % dset_patterns
        )


def main():
    """Runs argparse for ``fft_file``.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Interface for `fft_file`")
    parser.add_argument("input", type=str, help="Name of the input hdf5 file.")
    parser.add_argument(
        "output",
        type=str,
        help="Name of the output hdf5 file."
        " FFT is placed in the same dataset as in the input file."
        " Currently only looks for `local_current` datasets",
    )
    parser.add_argument(
        "--max-momentum",
        "-m",
        type=int,
        default=5,
        help="Name of the output hdf5 file."
        " FFT is placed in the same dataset as in the input file. [default=%(default)s]",
    )
    parser.add_argument(
        "--chunk-size",
        "-s",
        type=int,
        default=None,
        help="Number of first data set dimension array entries to read in at a time."
        " Reduces memory loads and defaults to whole data set. [default=%(default)s]",
    )
    parser.add_argument(
        "--overwrite",
        "-f",
        action="store_true",
        default=False,
        help="Overwrite hdf5 files if they already exist. [default=%(default)s]",
    )
    args = parser.parse_args()
    fft_file(
        args.input,
        args.output,
        max_momentum=args.max_momentum,
        chunk_size=args.chunk_size,
        overwrite=args.overwrite,
    )


if __name__ == "__main__":
    main()
