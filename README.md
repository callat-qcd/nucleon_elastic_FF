# three correlation function data management

This repo supports the generation of xml and tasks for our MDWF on HISQ calculations of the proton 3pt functions.
Currently, the task management scripts live in the `scripts` folder and are run as command line scripts.  Additionally, simple data collection scripts are also in the `scripts` folder and can be run as command line scripts.  ChrisK has developed a time-slicing script, that is run by first `pip install`ing, and then executed from the command line.

## scripts
[Andre add some description]

## 4D data management scripts

### install

Instantiate each time or add to your .bashrc/.bash_profile (this is for Summit)
```
module load python/3.7.0-anaconda3-5.3.0
export PYTHONUSERBASE=/ccs/proj/lgt100/c51/software/python
export PYTHONPATH="$PYTHONUSERBASE/lib/python3.7/site-packages:$PYTHONPATH"
export PATH="$PYTHONUSERBASE/bin:$PATH"
```

Option 1 - create symlink so updates pulled to repo do not have to be re-installed
```
cd <path_to_script>/nucleon_elastic_FF
pip install --user -e .
```
A successful installation will place a few executables here (on Summit)
```
/ccs/proj/lgt100/c51/software/python/bin/
```

### usage

A sample use case on Summit
```
cd /gpfs/alpine/proj-shared/lgt100/c51/x_files/project_2/production/a15m310Lfaces_a
nucelff -h [to get a help message]
nucelff formfac_4D/300 -s [to slice only cfg 300]
```
The, we can average by running either of the following
```
nucelff formfac_4D_tslice/300 -a --n-expected-sources 24
nucelff formfac_4D/300 -a --n-expected-sources 24
```