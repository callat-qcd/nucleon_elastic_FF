"""Routines for array manipulations

Routines are mostly an interface for numpy or cupy.
"""
from typing import List
from typing import Tuple

import numpy as np

from nucleon_ff_data.utilities import set_up_logger

LOGGER = set_up_logger(__name__)

# Cupy captured becaus can only be installed if GPU is present
try:
    import cupy as cp  # pylint: disable=E0401

    USE_CUPY = True
except ImportError:
    LOGGER.warning("Failed to import `cupy`. Disable cupy option.")
    cp = None
    USE_CUPY = False


def average_arrays(arrays: List[np.ndarray]):
    """Avrages arrays
    """
    LOGGER.debug("Averaging arrays")
    return np.average(arrays, axis=0)


def slice_array(array: np.ndarray, index: List[int], axis: int = 0):
    """
    """
    LOGGER.debug("Slicing array with index `%s` and axis `%s`", index, axis)
    index_delete = [ind for ind in np.arange(array.shape[axis]) if ind not in index]
    return np.delete(array, index_delete, axis)


def shift_array(array: np.ndarray, shift: int = 0, axis: int = 0):
    """
    """
    LOGGER.debug("Shifting array by `%s` in axis `%s`", shift, axis)
    return np.roll(array, shift, axis)


def get_fft(
    array: np.ndarray, cuda: bool = False, axes: Tuple[int] = (1, 2, 3)
) -> np.ndarray:
    r"""Execute fft for input array over the axes `[1, 2, 3]`.

    For input $f(t, n_i)$, the transformation is defined by
    $$ f(t, k_i)
    =
    \\left(
    \\prod_{i=1}^3 \\sum_{n_i=0}^{N_i}
    \\exp \\left\\{ - \\frac{2 \\pi i}{N_i} n_i k_i \\right \\}
    \\right)
    f(t, n_i)
    $$

    **Arguments**
        mean: np.ndarray
            The source averaged input data of shape `[NT, NZ, NY, NX]`

        cuda: bool = False
            Use cupy to do fft transformation.
    """
    LOGGER.debug("Executing fft on axes `%s`", axes)
    if cuda and USE_CUPY:
        array_d = cp.asarray(array)
        fft_d = cp.fft.fftn(array_d, axes=axes)
        fft = cp.asnumpy(fft_d)
    else:
        fft = np.fft.fftn(array, axes=axes)
    return fft
