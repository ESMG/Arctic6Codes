#!/usr/bin/env python
# coding: utf-8

# TODO:
# - this program appears to leak memory!

# Subset ERA5 on the global grid to the Arctic12 domain
# Special calculations:
#   - Calculate Specific Humidity
#   - Calculate Total Rain Rate

# Program operation
# - Initialization
#   - Obtain ERA5 land mask from SST field
# For each year
#  - Subset
#  - Make periodic
#  - Flooding
#  - Pad prior year

import numpy as np
import xarray as xr
import sys, os, cftime, warnings, time
from glob import glob
from HCtFlood import kara as flood

# Get performance reports for dask
#  - use with syntax on a block of code
#   with performance_report(filename='dask-report.html'):
#
#       .... code ....
#
#  - requires global client variable
#
#from dask.distributed import Client
#from dask.distributed import performance_report
#client = Client(processes=False)

# Subsetting functions

# Functions for humidity borrowed and adapted from MetPy.calc:
# - https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.html
def mixing_ratio(partial_press, total_press, molecular_weight_ratio=0.622):
    return (molecular_weight_ratio * partial_press
                / (total_press - partial_press))


def specific_humidity_from_mixing_ratio(mr):
    return mr / (1 + mr)


def saturation_vapor_pressure(temperature):
    sat_pressure_0c = 6.112e2 # Pa
    return sat_pressure_0c * np.exp(17.67 * (temperature - 273.15) # K -> C
                                        / (temperature - 29.65))   # K -> C


def saturation_mixing_ratio(total_press, temperature):
    return mixing_ratio(saturation_vapor_pressure(temperature), total_press)


def make_periodic_append_longitude(ds, dsvar, delta_long, has_time=True, flip_latitude=False):
    # This appends a longitude point for the given variable

    # Append longitude to the longitude coordinate
    longitudes = list(ds['longitude'].values)
    new_longitude = (longitudes[-1] + delta_long)
    longitudes.append(new_longitude)

    print("  -> make_periodic")
    if has_time:
        ds_pad = ds.pad(longitude=(0,1))
        ds_pad[dsvar][:,:,-1] = ds_pad[dsvar][:,:,0]
        ds_pad = ds_pad.assign_coords(longitude=longitudes)
    else:
        # No time dimension
        ds_pad = ds.pad(longitude=(0,1))
        ds_pad[dsvar][:,-1] = ds_pad[dsvar][:,0]
        ds_pad = ds_pad.assign_coords(longitude=longitudes)

    # Reverse the latitudes
    if flip_latitude:
        ds_pad = ds_pad.reindex(latitude=list(reversed(ds_pad.latitude)))

    return ds_pad

def save_attrs(ds):

    attr_array = {}
    for dvar in list(ds.variables):
        attr_array[dvar] = ds[dvar].attrs

    return attr_array

def fix_encoding_attrs(ds, oldattrs):
    global datatype

    for dvar in list(ds.variables):
        ds[dvar].encoding.update({'dtype': datatype, '_FillValue': None})
        if 'missing_value' in ds[dvar].encoding: ds[dvar].encoding.pop('missing_value')
        if 'scale_factor' in ds[dvar].encoding: ds[dvar].encoding.pop('scale_factor')
        if 'add_offset' in ds[dvar].encoding: ds[dvar].encoding.pop('add_offset')
        ds[dvar].attrs = oldattrs[dvar]

        ds['time'].encoding.update({'calendar': 'gregorian'})

    return ds

# Flooding functions

def interp_landmask(landmask_file):
    landmask = xr.open_dataset(landmask_file).rename({'x': 'lon', 'y': 'lat'})
    lon_centers = landmask['lon'].values
    lat_centers = landmask['lat'].values
    lon_corners = 0.25 * (
        lon_centers[:-1, :-1]
        + lon_centers[1:, :-1]
        + lon_centers[:-1, 1:]
        + lon_centers[1:, 1:]
    )
    # have to add 2 extra rows/columns to the array becuase we remove 1 when we calculate the corners from the center values
    lon_corners_exp = np.full((lon_corners.shape[0]+2,lon_corners.shape[1]+2),np.nan)
    lon_corners_exp[:-2,:-2] = lon_corners
    landmask['lon_b'] = xr.DataArray(data=lon_corners_exp, dims=("nyp", "nxp"))
    lon_b = landmask['lon_b']
    filled = lon_b.interpolate_na(dim='nyp',method='linear',fill_value="extrapolate")
    filled_lon = filled.interpolate_na(dim='nxp',method='linear',fill_value="extrapolate")

    # interpolate latitidue corners from latitude cell centers
    lat_corners = 0.25 * (
        lat_centers[:-1, :-1]
        + lat_centers[1:, :-1]
        + lat_centers[:-1, 1:]
        + lat_centers[1:, 1:]
    )

    # create expanded latitude corners array and then interpolate the values so our nxp, nyp = nx+1, ny+1
    lat_corners_exp = np.full((lat_corners.shape[0]+2,lat_corners.shape[1]+2),np.nan)
    lat_corners_exp[:-2,:-2] = lat_corners
    landmask['lat_b'] = xr.DataArray(data=lat_corners_exp, dims=("nyp", "nxp"))
    lat_b = landmask['lat_b']
    filled= lat_b.interpolate_na(dim='nyp',method='linear',fill_value="extrapolate")
    filled_lat = filled.interpolate_na(dim='nxp',method='linear',fill_value="extrapolate")
    landmask['lon_b'] = filled_lon
    landmask['lat_b'] = filled_lat
    landmask['mask'] = landmask['mask'].where(landmask['mask'] != 1)

    return landmask

def interp_era5(era5_ds, era5_var):
    #era = xr.open_dataset(era5_file)
    era = era5_ds
    era = era.rename({'longitude': 'lon', 'latitude': 'lat'})
    if "lon" in era.coords:
        era = era.assign_coords(lon=(np.where(era['lon'].values > 180., era['lon'].values - 360, era['lon'].values)))
        era = era.swap_dims({'lon' : 'nx'})
        era = era.swap_dims({'lat' : 'ny'})
    if "lon" in era.data_vars:
        era['lon'].values =  np.where(era['lon'].values > 180., era['lon'].values - 360, era['lon'].values)

    lon_centers = era['lon'].values
    lat_centers = era['lat'].values
    # To use conservative regidding, we need the cells corners. 
    # Since they are not provided, we are creating some using a crude approximation. 
    lon_corners = 0.25 * (
        lon_centers[:-1]
        + lon_centers[1:]
        + lon_centers[:-1]
        + lon_centers[1:]
    )

    lat_corners = 0.25 * (
        lat_centers[:-1]
        + lat_centers[1:]
        + lat_centers[:-1]
        + lat_centers[1:]
    )

    # trim down era by 1 cell
    era = era.isel(nx=slice(1,-1), ny=slice(1,-1))
    da_era_var=era[era5_var].values

    # add nxp and nyp dimensions for the lat/lon corners to latch onto
    era = era.expand_dims({'nyp':(len(era.lat) + 1)})
    era = era.expand_dims({'nxp':(len(era.lon) + 1)})

    # add the lat/lon corners as data variables,
    era['lat_corners'] = xr.DataArray(data=lat_corners, dims=("nyp"))
    era['lon_corners'] = xr.DataArray(data=lon_corners, dims=("nxp"))
    # drop the variable
    era = era.drop_vars(era5_var)
    era[era5_var] = xr.DataArray(data=da_era_var, dims=("time" ,"lat", "lon"))

    # create meshgrids for center and corner points so we can co-locate with landmask meshgrids.
    lon2d, lat2d = np.meshgrid(era.lon.values, era.lat.values)
    lon2d_b, lat2d_b = np.meshgrid(era.lon_corners.values, era.lat_corners.values)

    # assign coordinates now that we have our corner points
    era = era.assign_coords({"lon" : (("ny", "nx"), lon2d)})
    era = era.assign_coords({"lat" : (("ny", "nx"), lat2d)})
    era = era.assign_coords({"lon_b" : (("nyp", "nxp"), lon2d_b)})
    era = era.assign_coords({"lat_b" : (("nyp", "nxp"), lat2d_b)})

    return era

def flood_era5_data(era5_ds, era5_var, dataset_landmask):

    era = era5_ds
    era = era.rename({'longitude':'lon', 'latitude':'lat'})

    # Use the ERA5 landmask to blank out interior data for filling via kara
    print("  -> era_cut")
    era_cut = era[era5_var].where(dataset_landmask['mask'].values == 0)

    # If debug is True, a single time slice is used for testing.
    # Use the ncview.sh to bring up views of the netCDF files.
    debug = False
    if debug:
        print("  -> flood (debug)")
        era_cut_one = era_cut.isel(time=0)
        era_cut_one.to_netcdf('era_cut.nc')

        flooded = flood.flood_kara(era_cut_one)
        flooded = flooded.isel(z=0).drop('z')

        flooded.to_netcdf('flood.nc')
    else:
        print("  -> flood")
        flooded = flood.flood_kara(era_cut)
        flooded = flooded.isel(z=0).drop('z')

    # Convert flooded grid to model grid (without the mask variable)
    #regrid_domain = xe.Regridder(flooded, landgrid, 'patch',
    #    periodic=True, reuse_weights=reuse_weights, filename='regrid_domain.nc',
    #    ignore_degenerate=True)

    #data = regrid_domain(flooded)

    #data.to_netcdf('regrid.nc')

    #breakpoint()

    # regrid conservatively: conservative does the best, especially along fine points
    #print("  -> Regridder")
    #regrid_domain = xe.Regridder(landmask, era, 'conservative', 
    #    periodic=False, reuse_weights=reuse_weights, filename='regrid_domain.nc')
    #print("  -> regrid_domain")
    #land_regrid = regrid_domain(landmask.mask)
    #land_regrid = land_regrid.expand_dims(time=era['time'])
    #land_regrid = land_regrid.transpose("time", "ny", "nx")
    #print(land_regrid)
    #era = era.transpose("time", "lat", "lon", "ny", "nx", "nyp", "nxp")
    # cut era based on regridded landmask
    #era_cut = era[era5_var].where(land_regrid.values == 0)

    # flood our cut out points
    #breakpoint()
    #flooded = flood.flood_kara(era_cut)
    #flooded = flooded.isel(z=0).drop('z')
    #print(flooded)
    # note that this current version of this code will cut down your era5 domain by 2 rows/cols)
    #era = xr.open_dataset(era5_file)
    #era = era5_ds
    #era = era.isel(longitude=slice(1,len(era.longitude)-1), latitude=slice(1,len(era.latitude)-1))
    #era = era.transpose("time", "latitude", "longitude")

    era[era5_var].values = flooded.values

    if era5_var=='ssrd' or era5_var=='strd':
        # convert radiation from J/m2 to W/m2: https://confluence.ecmwf.int/pages/viewpage.action?pageId=155337784
        era[era5_var].values = era[era5_var].values/3600
        era[era5_var].attrs['units'] = 'W m-2'
    if era5_var=='huss':
        era[era5_var].attrs['dtype'] = datatype
        era[era5_var].attrs['standard_name'] = 'specific_humidity'
        #era[era5_var].attrs['long_name'] = 'Near-Surface Specific Humidity'
        era[era5_var].attrs['long_name'] = '2 meter near-surface specific humidity'
        era[era5_var].attrs['coordinates'] = 'height'
        era[era5_var].attrs['units'] = 'kg kg-1'
        era['height'] = 2.0
        era['height'].attrs['units'] = "m"
        era['height'].attrs['axis'] = "Z"
        era['height'].attrs['positive'] = "up"
        era['height'].attrs['long_name'] = "height"
        era['height'].attrs['standard_name'] = "height"

    #era.to_netcdf(outfile,format='NETCDF4_CLASSIC')
    #era.close()

    return era

# Padding functions

def checkPadding(thisYear, pastYear, era_var, tmp_file=None):

    ty_ds = xr.open_dataset(thisYear)
    py_ds = xr.open_dataset(pastYear)

    # Check is past year is already padded
    doPadding = False
    t1 = ty_ds['time'][0]
    t2 = py_ds['time'][-1]

    # If the records are not the same, do some padding
    if not(t1.values == t2.values):
        doPadding = True

    #breakpoint()

    if doPadding:
        print("  -> pad")
        
        firstRec = ty_ds[era_var][0,:,:]
        py_ds_pad = py_ds.pad(time=(0,1))
        py_ds_pad[era_var][-1,:,:] = firstRec
        tcoord = py_ds_pad['time'].values
        tcoord[-1] = t1.values
        py_ds_pad = py_ds_pad.assign_coords(time=tcoord)
        newRecs = py_ds_pad

        # Remove all _FillValue
        all_vars = list(newRecs.data_vars.keys()) + list(newRecs.coords.keys())
        encodings = {v: {'_FillValue': None, 'dtype': datatype} for v in all_vars}
        encodings['time'].update({'calendar': 'gregorian'})

        ty_ds.close()
        py_ds.close()

        # In certain circumstances, overwriting a file causes problems.
        # Save to a temp file and rename.
        if tmp_file:
            newRecs.to_netcdf(tmp_file, format="NETCDF4_CLASSIC", encoding=encodings, unlimited_dims='time')
            os.unlink(pastYear)
            os.rename(tmp_file, pastYear)
        else:
            newRecs.to_netcdf(pastYear, format="NETCDF4_CLASSIC", encoding=encodings, unlimited_dims='time')
    else:
        ty_ds.close()
        py_ds.close()

# The processing order is set by this dictionary
era5_dict = {
    'ERA5_2m_temperature':                      't2m',
    'ERA5_sea_surface_temperature':             'sst',
    'ERA5_sea_ice_cover':                       'siconc',
    'ERA5_10m_u_component_of_wind':             'u10',
    'ERA5_10m_v_component_of_wind':             'v10',
    'ERA5_surface_solar_radiation_downwards':   'ssrd',
    'ERA5_surface_thermal_radiation_downwards': 'strd',
    'ERA5_mean_sea_level_pressure':             'msl',
    'ERA5_total_rain_rate':                     'trr',
    'ERA5_snowfall':                            'sf',
    'ERA5_2m_specific_humidity':                'huss',
}

# For testing, only process one field
#era5_dict = {
#    'ERA5_2m_temperature':                      't2m',
#    'ERA5_total_rain_rate':                     'trr'
#}

# subset
# Stage 1: Testing, just do two years (1993,1995)
# Stage 2: Run all years (1993,2019)
years = range(1993,1995)
latsub = slice(90,39)
lonsub = slice(0,360)

# storage
# NOT USED

# directories
#era5dir = "/import/AKWATERS/kshedstrom/ERA5"
era5dir = "/import/AKWATERS/jrcermakiii/data/ERA5"
subdir = "/import/AKWATERS/jrcermakiii/data/ERA5_periodic_subset"
modeldir = "/import/AKWATERS/jrcermakiii/configs/Arctic12/INPUT2"

# files
dataset_landmask_source_file = os.path.join(era5dir, "ERA5_sea_surface_temperature_1993.nc")
dataset_landmask_file = os.path.join(subdir, 'ERA5_landmask.nc')

# constants and flags
datatype = 'float32'
usePadding = True
useFlooding = True

# Padding is required for MOM6 to provide continuity between restarts of
# runs between blocks of time (in this case by year).
firstYear=1993

if not(os.path.isfile(dataset_landmask_file)):
    # Obtain landmask from ERA5 dataset
    # and subset
    print("Extracting dataset land mask.")
    ds_data = xr.open_dataset(dataset_landmask_source_file).sel(latitude=latsub, longitude=lonsub)

    ds_data['mask'] = xr.DataArray(
        data = np.where(np.isnan(ds_data['sst'][0,:,:].values),1,0),
        dims = ['latitude','longitude']
    )

    dataset_landmask = ds_data['mask'].copy()
    dataset_landmask = dataset_landmask.to_dataset()
    dataset_landmask['mask'].attrs['units'] = 'dataset landmask'
    dataset_landmask = make_periodic_append_longitude(dataset_landmask, 'mask', 0.25, has_time=False,
        flip_latitude=True)
    all_vars = list(dataset_landmask.data_vars.keys()) + list(dataset_landmask.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}
    dataset_landmask.to_netcdf(dataset_landmask_file, mode='w', format='NETCDF4_CLASSIC', encoding=encodings)
else:
    dataset_landmask = xr.open_dataset(dataset_landmask_file)

# Main program
for f in era5_dict.keys():
    print(f)
    for y in years:

        print("-> %d" % (y))

        # These two fields require special processing
        if f == 'ERA5_total_rain_rate':
            # Determine filenames for storage
            thisYear = os.path.join(subdir, f + '_' + str(y) + ".nc")
            pastYear = os.path.join(subdir, f + '_' + str(y-1) + ".nc")

            # Subset and flood if necessary
            if not(os.path.isfile(thisYear)):
                #breakpoint()
                try:
                    crr = xr.open_dataset(os.path.join(era5dir, 'ERA5_convective_rain_rate_' + str(y) + '.nc')).sel(latitude=latsub, longitude=lonsub)
                    lsrr = xr.open_dataset(os.path.join(era5dir, 'ERA5_large_scale_rain_rate_' + str(y) + '.nc')).sel(latitude=latsub, longitude=lonsub)
                except:
                    continue
                print("  -> subset")
                trr = xr.Dataset()
                trr['trr'] = crr['crr'] + lsrr['lsrr']
                trr['trr'].attrs = {'units': 'kg m-2 s-1', 'long_name': 'Total rain rate (convective and large scale)'}
                trr = make_periodic_append_longitude(trr, era5_dict[f], 0.25, flip_latitude=True)

                # Flood
                if useFlooding:
                    trr = flood_era5_data(era5_ds=trr, era5_var='trr', dataset_landmask=dataset_landmask)

                # Remove all _FillValue
                all_vars = list(trr.data_vars.keys()) + list(trr.coords.keys())
                encodings = {v: {'_FillValue': None, 'dtype': datatype} for v in all_vars}

                # Also fix the time encoding
                encodings['time'].update({'dtype': datatype, 'calendar': 'gregorian', 'units': 'hours since 1900-01-01 00:00:00'})

                trr.to_netcdf(thisYear, mode='w', format='NETCDF4_CLASSIC', encoding=encodings, unlimited_dims='time')
                crr.close()
                lsrr.close()
                trr.close()

            # Pad
            # For ERA5, years after the first year, the first record of the recently processed year has to be
            # appended to the prior year.  This routine can be smart by checking if the prior year has already
            # been padded.
            if usePadding and y > firstYear:
                checkPadding(thisYear, pastYear, era5_dict[f])

        if f == 'ERA5_2m_specific_humidity':
            # Determine filenames for storage
            thisYear = os.path.join(subdir, f + '_' + str(y) + ".nc")
            pastYear = os.path.join(subdir, f + '_' + str(y-1) + ".nc")

            # Subset and flood if necessary
            if not(os.path.isfile(thisYear)):
                #breakpoint()
                try:
                    pair = xr.open_dataset(os.path.join(era5dir, 'ERA5_surface_pressure_' + str(y) + '.nc'))['sp'].sel(latitude=latsub, longitude=lonsub) # Pa
                    tdew = xr.open_dataset(os.path.join(era5dir, 'ERA5_2m_dewpoint_temperature_' + str(y) + '.nc'))['d2m'].sel(latitude=latsub, longitude=lonsub) # K
                except:
                    continue

                print("  -> subset")
                smr = saturation_mixing_ratio(pair, tdew)
                sphum = specific_humidity_from_mixing_ratio(smr)

                sphum.name = 'huss'
                sphum = sphum.to_dataset()
                sphum['huss'].attrs['units'] = 'kg kg-1'
                sphum['huss'].attrs['long_name'] = '2 meter specific humidity'
                sphum = make_periodic_append_longitude(sphum, era5_dict[f], 0.25, flip_latitude=True)

                # Flood
                if useFlooding:
                    sphum = flood_era5_data(era5_ds=sphum, era5_var='huss', dataset_landmask=dataset_landmask)

                # Remove all _FillValue
                all_vars = list(sphum.data_vars.keys()) + list(sphum.coords.keys())
                encodings = {v: {'_FillValue': None, 'dtype': datatype} for v in all_vars}

                # Also fix the time encoding
                encodings['time'].update({'dtype': datatype, 'calendar': 'gregorian', 'units': 'hours since 1900-01-01 00:00:00'})

                sphum.to_netcdf(
                    thisYear,
                    format='NETCDF4_CLASSIC',
                    engine='netcdf4',
                    encoding=encodings,
                    unlimited_dims='time'
                )
                sphum.close()

            # Pad
            # For ERA5, years after the first year, the first record of the recently processed year has to be
            # appended to the prior year.  This routine can be smart by checking if the prior year has already
            # been padded.
            if usePadding and y > firstYear:
                tmp_file = os.path.join(subdir, f + '_' + str(y-1) + "_tmp.nc")
                checkPadding(thisYear, pastYear, era5_dict[f], tmp_file=tmp_file)

        # All other fields conform to a single processing method
        if 'total_rain_rate' not in f and 'specific_humidity' not in f:
            # Determine filenames for storage
            thisYear = os.path.join(subdir, f + '_' + str(y) + ".nc")
            pastYear = os.path.join(subdir, f + '_' + str(y-1) + ".nc")

            # Subset and flood if necessary
            if not(os.path.isfile(thisYear)):
                #breakpoint()
                ds_file = os.path.join(era5dir, f + '_' + str(y) + ".nc")
                try:
                    ds = xr.open_dataset(ds_file).sel(latitude=latsub, longitude=lonsub)
                except:
                    continue
                print("  -> subset")
                ds_attrs = save_attrs(ds)
                ds = make_periodic_append_longitude(ds, era5_dict[f], 0.25, flip_latitude=True)
                ds = fix_encoding_attrs(ds, ds_attrs)

                # Flood
                if useFlooding:
                    ds = flood_era5_data(era5_ds=ds, era5_var=era5_dict[f], dataset_landmask=dataset_landmask)

                ds.to_netcdf(thisYear, format="NETCDF4_CLASSIC", unlimited_dims='time')
                ds.close()

            # Pad
            # For ERA5, years after the first year, the first record of the recently processed year has to be
            # appended to the prior year.  This routine can be smart by checking if the prior year has already
            # been padded.
            if usePadding and y > firstYear:
                checkPadding(thisYear, pastYear, era5_dict[f])


#time.sleep(600)
