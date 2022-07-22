#!/usr/bin/env python

import xarray as xr
import numpy as np
import datetime
import os, sys, glob
import argparse

def getArguments():
    '''
    Process command line arguments.

    --srcDir=Source directory
    --dstDir=Destination directory
    --doYear=YYYY
    --pad=YYYY,YYYY or --pad=YYYY

    NOTE: Padding is always in perspective of the current year or past year.  
    (A) If the prior year is given, the first record of the current year is
        appended to the prior year.
    (B) If the current year is given, the last record of the prior year is
        prepended to the current year.
    '''

    parser = argparse.ArgumentParser(description='Process daily Glorys OBCs')
    parser.add_argument("--srcDir", help='Source directory', type=str, default=None)
    parser.add_argument("--dstDir", help='Destination directory', type=str, default=None)
    parser.add_argument("--doYear", help='Year of data to combine', type=int, default=None)
    parser.add_argument("--fixStartTime", help='Ensure hour of first record is midnight', type=bool, default=False)
    parser.add_argument("--fixEndTime", help='Ensure date of last record ends at midnight', type=bool, default=False)
    parser.add_argument("--pad", help='Year or years in which to perform padding', type=str, default=None)

    args = parser.parse_args()
    return args

def checkPadding(ds, ds_attr):
    '''
    Check for padding in given dataset.
    checkPadding(priorYear, 'padEnd')
    '''
    rec = 0

    if ds_attr == 'padStart':
       rec = 0
       # If padding was already done, use next record
       if 'time' in ds.variables:
           if ds_attr in ds['time'].attrs:
               if ds['time'].attrs[ds_attr] == 1:
                   rec = 1

    if ds_attr == 'padEnd':
       rec = -1 
       # If padding was already done, use next record
       if 'time' in ds.variables:
           if ds_attr in ds['time'].attrs:
               if ds['time'].attrs[ds_attr] == 1:
                   rec = -2

    #breakpoint()
    return rec

# Enforce float32 or int32
def get_dtype(vName, vrbName, nc_int, nc_float):
    vrbDtype = nc_int
    if vName in vrbName or 'lat' in vrbName or 'lon' in vrbName\
        or 'u_segment' in vrbName or 'v_segment' in vrbName:
        vrbDtype = nc_float

    return vrbDtype

def main():

    args = getArguments()
    dstDir = args.dstDir
    yr = args.doYear
    nc_fmt = 'NETCDF4'
    nc_float = np.float32
    nc_int = np.int32

    if args.pad:
        padYears = [int(yr) for yr in args.pad.split(',')]

    # Collect files to merge using xr.open_mfdataset()
    varNames = ['salt', 'temp', 'uv', 'zeta']

    for seg in range(1,5):
        print("->",seg)
        for vName in varNames:
            destFile = f'{dstDir}/{vName}_00{seg}.nc'
            tmpdestFile = f'{dstDir}/{vName}_00{seg}_tmp.nc'
            doMerge = False
            
            if not(os.path.isfile(destFile)):
                doMerge = True

            if doMerge:
                print("  ->",vName,"merge")

                fileNames = sorted(glob.glob(os.path.join(args.srcDir,f'{vName}_00{seg}_{yr}*')))
                nfiles = len(fileNames)
                if nfiles < 365 or nfiles > 366:
                    print("Inconsistent number of files found:",nfiles)
                    sys.exit()
                mergedData = xr.open_mfdataset(fileNames)
                #breakpoint()
                # Temporary one off
                if vName == 'zeta':
                    vrbs = list(mergedData.keys())
                    for vrb in vrbs:
                        if vrb.find("_zos_") >= 0:
                            vrbOrig = vrb
                            vrbNew = vrb.replace("_zos_","_zeta_")
                            mergedData = mergedData.rename({vrbOrig: vrbNew})
                encodings = {}
                for vrbName in list(mergedData.variables):
                    vrbDtype = get_dtype(vName, vrbName, nc_int, nc_float)
                    encodings[vrbName] = {'_FillValue': None, 'dtype': vrbDtype}
                encodings['time'] = {'_FillValue': None}
                encodings['time'].update({'dtype': nc_float, 'calendar': 'gregorian'})

                # If fixStartTime is True, make sure the time coordinate of the first record is
                # midnight.  Use the special .dt accessor to get to date and time components.
                # Updating values used as coordinates is harder than plain variables.
                if args.fixStartTime:
                    begOfYear = xr.DataArray(datetime.datetime(yr, 1, 1))
                    firstRec = mergedData['time'][0]
                    currentHour = float(firstRec.dt.hour)
                    if currentHour != 0.0:
                        diffSec = int((firstRec - begOfYear).dt.seconds)
                        if diffSec > (60 * 60 * 24):
                            print("ERROR: Adjustment period too large?", begOfYear.data, firstRec.data)
                            sys.exit()
                        print("    - Adjusting first record time coordinate by", diffSec, "seconds.")
                        md = mergedData['time'].data
                        md[0] = (firstRec - np.timedelta64(diffSec, 's')).data
                        mdUpd = mergedData.assign_coords({'time':('time',md,mergedData['time'].attrs)})
                        mergedData = mdUpd

                # If fixEndTime is True, make sure the time coordinate of the
                # last record is midnight of the following year.  Use the
                # special .dt accessor to get to date and time components.  Updating 
                # values used as coordinates is harder than plain variables.
                if args.fixEndTime:
                    begOfNextYear = xr.DataArray(datetime.datetime(yr+1, 1, 1))
                    lastRec = mergedData['time'][-1]
                    currentHour = float(lastRec.dt.hour)
                    if currentHour != 0.0:
                        diffSec = int((begOfYear - lastRec).dt.seconds)
                        if diffSec > (60 * 60 * 24):
                            print("ERROR: Adjustment period too large?", begOfYear.data, lastRec.data)
                            sys.exit()
                        print("    - Adjusting last record time coordinate by", diffSec, "seconds.")
                        md = mergedData['time'].data
                        md[-1] = (lastRec - np.timedelta64(diffSec, 's')).data
                        mdUpd = mergedData.assign_coords({'time' : ('time', md, mergedData['time'].attrs)})
                        mergedData = mdUpd

                # Reset time valid_min and valid_max attributes
                #breakpoint()
                mergedData['time'].attrs['valid_min'] = mergedData['time'].min().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']
                mergedData['time'].attrs['valid_max'] = mergedData['time'].max().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']

                mergedData.to_netcdf(destFile, encoding=encodings,
                    unlimited_dims='time', format=nc_fmt)
                #breakpoint()
            else:
                mergedData = xr.open_dataset(destFile)

            # Perform padding as needed
            if args.pad:
                prior_yr = yr - 1

                for padYear in padYears:

                    # Do padding for current year
                    if padYear == yr:
                        doPadding = False
                        padFile = f'{prior_yr}/{vName}_00{seg}.nc'
                        priorYear = xr.open_dataset(padFile)

                        # Check this year to see if the record has already been appended
                        # Check if records have been padded? If not, set doPadding True
                        priorYearRec = checkPadding(priorYear, 'padEnd')
                        thisYearRec = 0

                        #print("Padding", padYear, priorYearRec, thisYearRec)
                        doPadding = bool(priorYear['time'][priorYearRec] != mergedData['time'][thisYearRec])

                        if doPadding:
                            print("  ->",vName,"padding")

                            newMergedData = xr.Dataset()

                            # if padding needs to be done, we copy 
                            # priorYear['time'][priorYearRec] to record zero of
                            # mergedData.
                            # Collect variable names and coordinate names
                            varNamesPad = list(set(list(mergedData.variables)) - set(list(mergedData.coords)))
                            crdNamesPad = list(mergedData.coords)

                            # Loop through variables and merge items through concatenation
                            # priorYear[priorYearRec] + mergedData
                            #breakpoint()
                            for varNamePad in varNamesPad:
                                priorRec = priorYear[varNamePad][priorYearRec:priorYearRec+1]
                                catRec = xr.concat([priorRec, mergedData[varNamePad]], "time")
                                newMergedData[varNamePad] = catRec

                            # Update metadata
                            # Mark that we padded the prior year
                            newMergedData['time'].attrs['valid_min'] = newMergedData['time'].min().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']
                            newMergedData['time'].attrs['valid_max'] = newMergedData['time'].max().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']
                            newMergedData['time'].attrs['padStart'] = np.int32(1)

                            # Save a temporary netCDF file and overwrite the destFile
                            encodings = {}
                            for vrbName in list(newMergedData.variables):
                                vrbDtype = get_dtype(vName, vrbName, nc_int, nc_float)
                                encodings[vrbName] = {'_FillValue': None, 'dtype': vrbDtype}
                                if vrbName == 'time':
                                   encodings[vrbName]['calendar'] = 'gregorian'
                                   encodings[vrbName]['dtype'] = nc_float

                            #breakpoint()
                            # We may need to reorder_levels to put time back in its proper place.
                            # Original data: salt_segment_001(time, nz_segment_001, ny_segment_001, nx_segment_001)
                            # After concat:  salt_segment_001(nz_segment_001, ny_segment_001, nx_segment_001, time)
                            newMergedData.to_netcdf(tmpdestFile, encoding=encodings,
                                unlimited_dims='time', format=nc_fmt)
                            mergedData.close()
                            os.unlink(destFile)
                            os.rename(tmpdestFile, destFile)
                            mergedData = xr.open_dataset(destFile)

                        priorYear.close()

                    # Do padding for prior year
                    if padYear == prior_yr:
                        doPadding = False
                        padFile = f'{prior_yr}/{vName}_00{seg}.nc'
                        priorYear = xr.open_dataset(padFile)

                        # Check the prior year to see if the record has already been appended
                        # Check if records have been padded? If not, set doPadding True
                        priorYearRec = -1
                        thisYearRec = checkPadding(mergedData, 'padStart')

                        #print("Padding", padYear, priorYearRec, thisYearRec)
                        doPadding = bool(priorYear['time'][priorYearRec] != mergedData['time'][thisYearRec])

                        if doPadding:
                            print("  ->",vName,"padding")

                            # Create empty padded dataset
                            padPriorYear = xr.Dataset()
                    
                            # Collect variable names and coordinate names
                            varNamesPad = list(set(list(priorYear.variables)) - set(list(priorYear.coords)))
                            crdNamesPad = list(priorYear.coords)

                            # Loop through variables and merge items through concatenation
                            # priorYear + mergedData[thisYearRec]
                            for varNamePad in varNamesPad:
                                firstRec = mergedData[varNamePad][thisYearRec:thisYearRec+1]
                                priorRec = priorYear[varNamePad]
                                padPriorYear[varNamePad] = xr.concat([priorRec, firstRec], "time")

                            #breakpoint()
                            # Update metadata
                            # Mark that we padded the prior year
                            padPriorYear['time'].attrs['valid_min'] = padPriorYear['time'].min().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']
                            padPriorYear['time'].attrs['valid_max'] = padPriorYear['time'].max().dt.strftime('%Y-%m-%d %H:%M:%S').to_dict()['data']
                            padPriorYear['time'].attrs['padEnd'] = np.int32(1)

                            encodings = {}
                            for vrbName in list(padPriorYear.variables):
                                vrbDtype = get_dtype(vName, vrbName, nc_int, nc_float)
                                encodings[vrbName] = {'_FillValue': None, 'dtype': vrbDtype}
                                if vrbName == 'time':
                                   encodings[vrbName]['calendar'] = 'gregorian'
                                   encodings[vrbName]['dtype'] = nc_float

                            # Release resources
                            priorYear.close()

                            # Overwrite the original file
                            padPriorYear.to_netcdf(padFile, encoding=encodings,
                                unlimited_dims='time', format=nc_fmt)
                        else:
                            # Release resources
                            priorYear.close()

            # Release resources
            mergedData.close()

if __name__ == '__main__':
    main()
