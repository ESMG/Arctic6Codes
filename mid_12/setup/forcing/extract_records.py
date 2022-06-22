import os, sys
import xarray as xr

era5dir = "/import/AKWATERS/kshedstrom/ERA5"
trec = slice(0,19)

for yr in range(1993,1995):

    df = "ERA5_sea_surface_temperature_%d.nc" % (yr)
    dataset_source_file = os.path.join(era5dir, df)
    dataset_file = df

    # Extract the first X records of given years
    # (two or more records allow the time dimension to be retained)

    ds = xr.open_dataset(dataset_source_file)
    recs = ds['sst'][trec,:,:].to_dataset()

    # Avoid _FillValues
    all_vars = list(recs.data_vars.keys()) + list(recs.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}

    recs.to_netcdf(dataset_file, encoding=encodings)
