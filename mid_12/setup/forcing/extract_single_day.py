import os, sys
import xarray as xr

era5dir = "/import/AKWATERS/kshedstrom/ERA5"
dataset_source_file = os.path.join(era5dir, "ERA5_sea_surface_temperature_1993.nc")
dataset_file = 'ERA5_sea_surface_temperature_19930101.nc'

# Extract the first record which should be the first day of 1993

ds = xr.open_dataset(dataset_source_file)
one_rec = ds['sst'][0,:,:].to_dataset()

# Avoid _FillValues
all_vars = list(one_rec.data_vars.keys()) + list(one_rec.coords.keys())
encodings = {v: {'_FillValue': None} for v in all_vars}

one_rec.to_netcdf(dataset_file, encoding=encodings)
