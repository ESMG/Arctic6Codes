# forcing

Atmospheric forcing file generation for Arctic12 model run.

NOTE: These fields can be used in any of the Arctic runs.

# Scripts

## extract_records.py

This script extracts two records from an ERA5 grid.  This is used for
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
