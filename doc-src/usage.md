<<<<<<< HEAD
# Usage guid

## Usage of data management scripts
=======
# Usage of data management scripts
>>>>>>> Added doc parsing files

A sample use case on Summit
```
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a15m310Lfaces_a
nucelff -h [to get a help message]
nucelff formfac_4D/300 -s [to slice only cfg 300]
nucelff formfac_4D_tslice/300 -a --n-expected-sources 24
```
<<<<<<< HEAD

## Run tests
Run
```bash
python setup.py test
```
in the repository root.

If you are on `summit`, this also runs the legacy tests which compares
files created by the routine against benchmark files.
This could take roughly 2 minutes. 
=======
>>>>>>> Added doc parsing files
