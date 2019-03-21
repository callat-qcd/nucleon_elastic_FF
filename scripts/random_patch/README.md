# Random patch

The commit `0e9a50064f19b3ef10e7a5c475535ff9b403adf6` version (and before) of the `mdwf_hisq_pydb` repo use pythons `random` module to set the `seed` for reproducible stochastic computations.
The random seed was initialized with a string which causes compatibility issues when migrating from python2 to python3.
This module tries to restore compatibility.

## TL;DR
Do this in your code and you are fine.
```python
import os
os.environ["PYTHONHASHSEED"] = "0"
import random_patch as random
```

## Problem

### Hashing
When setting the seed of random by string, the string is hashed [[Python2]](https://docs.python.org/2/library/random.html#random.seed), [[Python3]](https://docs.python.org/3/library/random.html#random.seed).

The hash function was changed from version 2.7 compared to 3.4

> There are two changes in `hash()` function between Python 2.7 and Python 3.4
>
> 1. Adoptions of SipHash
> 2. Default enabling of Hash randomization
> ---
> References:
>
>  * Since from Python 3.4, it uses [SipHash](https://131002.net/siphash/) for it's hashing function. Read: [Python adopts SipHash](https://lwn.net/Articles/574761/)
>  * Since Python 3.3 Hash randomization is enabled by default. Reference: [object.__hash__](https://docs.python.org/3/reference/datamodel.html#object.__hash__) (last line of this > section). Specifying [PYTHONHASHSEED](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONHASHSEED) the value 0 will disable hash randomization.

[https://stackoverflow.com/a/40137700](https://stackoverflow.com/a/40137700)

This means

1. Setting the seed by string will not return the same result in python2 and python3
2. Setting the seed by string in python3 is not reproducible unless explicitly specified

### Random integers
Furthermore, I have encountered that even if you use the same random seed in python2 and python3, this does not mean that `random.randomint` will return the same integers.
This method has changed as well.
References:
[[Github issues DEAP]](https://github.com/DEAP/deap/issues/138#issue-157970911), [[`random.randomint`]](https://docs.python.org/3/library/random.html#random.randint)

> `random.randint(a, b)`
>   Return a random integer N such that `a <= N <= b`. Alias for `randrange(a, b+1)`.
> Changed in version 3.2: `randrange()` is more sophisticated about producing equally distributed values. Formerly it used a style like `int(random()*n)` which could produce slightly uneven distributions.

### Recommendation
For these two reasons, I strongly encourage to

1. NOT use a string to initialize a seed,
2. NOT use pythons `random` module for reproducible randomness.

Instead, it is better practice to

1. use integers to initialize a seed,
2. use, e.g., `numpy`s random module for reproducible randomness.


## Backwards compatible solutions
I have coded up backwards compatible solution.

The python3 seed is computed in a backwards compatible way and the random integers are computed as in python 2. See the `__init__.py` file.

See [http://pythoncentral.io](http://pythoncentral.io) for the implementation details.

### Usage
keep this directory `random_patch` and import it as the default `random` module.
```python
import random_patch as random
```
And set the environment variable "PYTHONHASHSEED=0".

## Tests
See the `tests.py` module in this directory for confirmation of my statements:
```
pytest tests.py
```
This depends on the `pytest` module.
