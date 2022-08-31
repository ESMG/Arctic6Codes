# OBC

Requires:
 * gridtools
   * `conda env create -f=conda/gridTools_export-linux-64.yml`
 * https://github.com/raphaeldussin/HCtFlood
   * Increase limit from 1000 to 2000 iterations in `flood_kara_raw` (HCtFlood/kara.py)
   * pip install -e .
 * bottleneck
   * conda install bottleneck

NOTE: Unfortunately, paths are hardcoded at the moment!

# GLORYS

Kate downloaded two halves of the earth in a glorys and glorys2 directory.  That is what we
are using for the OBCs.  The information is subset upfront before OBC processing is done.

# Running on a single node

## First day

```
python generate_obc_glorys2.py --flooding=True --date=1993-01-01 --firstRec=True --doYear=1993 --procDir=/home/cermak/workdir/configs/Arctic12/OBC/obc_gen/1993 --procDays 1
```

## Subsequent days

```
python generate_obc_glorys2.py --flooding=True --date=1993-01-01 --doYear=1993 --procDir=/home/cermak/workdir/configs/Arctic12/OBC/obc_gen/1993 --startDate=1993-01-02 --procDays 1
```

# Running on a cluster

This script creates slurm jobs to be run on Chinook:

```
python chkYear.py --procDir obc_gen --jobDir jobs --templateScript template.slurm\
  --doYear 1994\
  --showJobs True --createJobs True --maxDays 19
```

## dtypes

 * time: not integer, float (np.float32)
 * No int64 variables (np.int32)
 * No attribute with long integers (LL will show via ncdump)
   * Use np.int32() to create a single precision attribute

# Post processing

The way padding should work is each year block has to have a full year block
whether you fudge the first or last record.  For intermediate records, records
can be copied forward and backward to make complete years.

The behavior of padding can be changed depending on the years provided.  Padding
is done from the perspective of the current year being processed.  Use the `--pad`
argument.

 * If the prior year is provided, the first record of the current year is appended
   to the prior year.
 * If the current year is provided, the last record of the prior year is prepended to
   the current year.

## First year

```
python ../combine_year.py --doYear 1993 --srcDir p1993 --dstDir 1993 --fixStartTime True
```

## Subsequent years

Two things have to happen for GLORYS.
 * The first record of 1994 has to be appended to 1993
 * The last record of 1993 has to be prepended to 1994

```
python ../combine_year.py --doYear 1994 --srcDir p1994 --dstDir 1994 --pad 1993,1994
```

## Last year

```
python ../combine_year.py --doYear 2020 --srcDir p2020 --dstDir 2020 --pad 2019,2020 --fixEndTime True
```
