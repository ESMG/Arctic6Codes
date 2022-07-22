# OBC

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
