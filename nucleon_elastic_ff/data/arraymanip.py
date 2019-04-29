"""Routines for array manipulations

Routines are mostly an interface for numpy or cupy.
"""
from typing import List
from typing import Tuple

import numpy as np

from nucleon_elastic_ff.utilities import set_up_logger

LOGGER = set_up_logger("nucleon_elastic_ff")

# Cupy captured becaus can only be installed if GPU is present
try:
    import cupy as cp  # pylint: disable=E0401

    USE_CUPY = True
except ImportError:
    LOGGER.warning("Failed to import `cupy`. Disable cupy option.")
    cp = None
    USE_CUPY = False


def average_arrays(arrays: List[np.ndarray], axis: int = 0) -> np.ndarray:
    """Averages arrays over specified dimension. Input can be a list.

    arrays: List[np.ndarray]
        The arrays to average.

    axis: int = 0
        The average dimension index.
    """
    LOGGER.debug("Averaging arrays")
    return np.average(arrays, axis=axis)


def shift_array(array: np.ndarray, shift: int = 0, axis: int = 0) -> np.ndarray:
    """Rolls the array in specified dimension by shift: `v[n] -> v[n+shift]`

    array: List[np.ndarray]
        The arrays to average.

    shift: int
        The amount to shift.

    axis: int = 0
        The shift dimension index.
    """
    LOGGER.debug("Shifting array by `%s` in axis `%s`", shift, axis)
    return np.roll(array, shift, axis)


def get_fft(
    array: np.ndarray, axes: Tuple[int] = (1, 2, 3), cuda: bool = False
) -> np.ndarray:
    r"""Execute fft for input array over specified axes.

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

        axes: Tuple[int] = (1, 2, 3)
            The axes on which the fft is executed.

        cuda: bool = False
            Use cupy to do fft transformation.
    """
    LOGGER.debug("Executing fft on axes `%s`", axes)

    norm = 1
    for ind in axes:
        norm *= array.shape[ind]

    if cuda and USE_CUPY:
        array_d = cp.asarray(array)
        fft_d = cp.fft.ifftn(array_d, axes=axes)
        fft = cp.asnumpy(fft_d)
    else:
        fft = np.fft.ifftn(array, axes=axes)
    return fft * norm
