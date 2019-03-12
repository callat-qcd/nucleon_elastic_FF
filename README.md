# three_points


## nucleon_elastic_ff.data

Management scripts for nucleon elastic form factor data.

### Time slicing

Slicing h5 files in ther temporal component.


```python
from nucleon_elastic_ff.data.scripts.tslice import tslice

tslice(DATAROOT)
```

```
def tslice(
    root: str,
    name_input: str = "formfac_4D",
    name_output: str = "formfac_4D_tslice",
    overwrite: bool = False,
):
    """Recursively scans directory for files slices matches in time direction.

    The input files must be h5 files (ending with ".h5") and must have `name_input`
    in their file name. Files which have `name_output` as name are excluded.
    Also, this routine ignores exporting to files which already exist.
    Once all files are fixed, this routine calls `slice_file` on each file.
    The slicing info is inferred by the group name (see `parse_t_info`) and cut according
    using `slice_array`.

    **Arguments**
        root: str
            The directory to look for files.

        name_input: str = "formfac_4D"
            Files must match this pattern to be submitted for slicing.

        name_output: str = "formfac_4D_tslice"
            Files must not match this pattern to be submitted for slicing.
            Also the sliced output files will have the input name replaced by the output
            name. This also includes directory names.

        overwrite: bool = False
            Overwrite existing sliced files.
    """
```
