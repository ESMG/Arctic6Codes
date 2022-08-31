#!/usr/bin/env python

# Perform an inventory of glorys files
# DIR1 = /import/AKWATERS/kshedstrom/glorys
# DIR2 = /import/AKWATERS/kshedstrom/glorys2

# Scan for which years are present
# Example:
# /import/AKWATERS/kshedstrom/glorys/GLORYS_REANALYSIS_1993-01-01.nc

import os, sys, glob
import datetime

years_present = []
sdir = []

# Directory 1
#sdir.append('/import/AKWATERS/kshedstrom/glorys')
sdir.append('/home/cermak/data/glorys')
in_files = glob.glob(os.path.join(sdir[0], "*.nc"))
in_files.sort()
for inf in in_files:
    #breakpoint()
    fyr = os.path.basename(inf)[18:22]
    if not(fyr) in years_present:
        years_present.append(fyr)

# Directory 2
#sdir.append('/import/AKWATERS/kshedstrom/glorys2')
sdir.append('/home/cermak/data/glorys2')
in_files = glob.glob(os.path.join(sdir[1], "*.nc"))
in_files.sort()
for inf in in_files:
    fyr = os.path.basename(inf)[18:22]
    if not(fyr) in years_present:
        years_present.append(fyr)

print("Scanning GLORYS for missing files by year...")
#print(years_present)

for yr in years_present:
    beg = datetime.datetime(int(yr), 1, 1)
    dt = beg
    end = datetime.datetime(int(yr)+1, 1, 1)
    missing = []
    while dt < end:
        #breakpoint()
        for pth in sdir:
            fn = dt.strftime('GLORYS_REANALYSIS_%Y-%m-%d.nc')
            fp = os.path.join(pth, fn)
            if not(os.path.isfile(fp)):
                missing.append(fp)
        dt = dt + datetime.timedelta(days=1)

    #breakpoint()
    if len(missing) > 0:
        print(yr)
        missing.sort()
        for fn in missing:
            print("  > %s" % (fn))
        print("  ")
