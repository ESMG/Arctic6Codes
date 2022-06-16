# Arctic6Codes
Companion repository for
[Arctic6](https://github.com/ESMG/Arctic6) for setup and post processing of model runs
at 6, 12 and 18km.

# Directories

The directory model follows the
[nwa25](https://github.com/jsimkins2/nwa25.git)
git repository.

The Arctic6 repository is actually a collection of three model runs at
different resolutions.  The Arctic6 is the primary model.  The Arctic12
and Arctic18 runs are subsets of Arctic6.

The majority of code development is done in support of running the Arctic6
model run.  Code for running subsets of Arctic6 should be nearly identical.

For the subset model runs, the Arctic12 code is the one in primary development.
The Arctic18 code should be nearly identical to the Arctic12 code.

## run

Runtime files for Arctic6, Arctic12 and Arctic18 can be found in the
[Arctic6](https://github.com/ESMG/Arctic6)
git repository.

# arctic_6

## setup

### forcing

Dataset: ERA5

The atmospheric forcing files should be shareable across all the
Arctic runs since the same global subset is used.  See `mid_12` for
the python code.

The forcing files are:
 - periodic (longitude)
 - interior land points are flooded using the kara method
 - time dimension is padded, except for last year

# mid_12

The python code for Arctic12 is based on code provided by the
[NWA25](https://github.com/jsimkins2/nwa25.git) git repository.

## misc

## setup

### boundary (OBCs)
### forcing (atmosphere)
### initial (ICs)

# coarse_18

The python code for Arctic18 should be nearly identical to the
Arctic12 code.
