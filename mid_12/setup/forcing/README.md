# forcing

Atmospheric forcing file generation for Arctic6 model run.

NOTE: These fields can be used in any of the Arctic runs.

## Padding

MOM6 requires whole blocks of time within each run.  So, if there is
a model run from 1993 to 2020, and each run is one year, the following
conditions must be met:

For 1993, the first record must be Jan 1, 1993 at 00Z.  The end of 1993
must contain the first record of 1994.  This padded record does not need
to be at 00Z.

If forcing records are daily at 12Z, we fudge the first record for 1993 by
setting the hour to 00Z.

The same will have to be done for the last record of 2020.  If the records
are daily at 12Z, the last record at Dec 31, 2020 at 12Z will be modified so
it ends Jan 1, 2021 at 00Z.

# Scripts

## extract_records.py

This script extracts two or more records from an ERA5 grid.  This is used for
debugging and development using a smaller input dataset.

## ncview.sh

There is a `debug` flag within `subset_calc_era5.py` that can be set to look at
a single time record of a field.  Run `subset_calc_era5.py` first with
`debug=True` and then run `ncview.sh` to show the era5 field cut out and the
result after kara flooding.

## subset_calc_era5.py

The `subset_calc_era5.py` performs the following operations:
 - creates a land mask file based on the sea surface temperature field
 - subsets the global field to the area required by the model run
 - makes the longitude coordinate periodic
 - performs a land flood of the subset using the land mask file using the kara method
 - pads the time dimension of the prior year with the first record of the current
   year being processed
 - The dimension `time` needs to be float or double.  It also needs to be UNLIMITED.
 - The values for latitude and longitude must increase along the dimension.
