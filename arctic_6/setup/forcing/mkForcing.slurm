#!/bin/bash
#SBATCH --partition=t1small
#SBATCH --nodes=1
#SBATCH --exclusive
#SBATCH --time=48:00:00
#SBATCH --constraint=[Broadwell]

# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/import/AKWATERS/jrcermakiii/local/miniconda3/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/import/AKWATERS/jrcermakiii/local/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/import/AKWATERS/jrcermakiii/local/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/import/AKWATERS/jrcermakiii/local/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

conda activate gridTools

cd /home/jrcermakiii/src/Arctic6Codes/arctic_6/setup/forcing

#python subset_calc_era5.py --startYear 1993 --endYear 1994
#python subset_calc_era5.py --startYear 1993 --endYear 1995
#python subset_calc_era5.py --startYear 1993 --endYear 1996
#python subset_calc_era5.py --startYear 1993 --endYear 1997
#python subset_calc_era5.py --startYear 1993 --endYear 1998
#python subset_calc_era5.py --startYear 1993 --endYear 1999
#python subset_calc_era5.py --startYear 1993 --endYear 2000
#python subset_calc_era5.py --startYear 1993 --endYear 2001
#python subset_calc_era5.py --startYear 1993 --endYear 2002
#python subset_calc_era5.py --startYear 1993 --endYear 2003
#python subset_calc_era5.py --startYear 1993 --endYear 2004
#python subset_calc_era5.py --startYear 1993 --endYear 2005
#python subset_calc_era5.py --startYear 1993 --endYear 2006
#python subset_calc_era5.py --startYear 1993 --endYear 2007
#python subset_calc_era5.py --startYear 1993 --endYear 2008
#python subset_calc_era5.py --startYear 1993 --endYear 2009
#python subset_calc_era5.py --startYear 1993 --endYear 2010
#python subset_calc_era5.py --startYear 1993 --endYear 2011
#python subset_calc_era5.py --startYear 1993 --endYear 2012
#python subset_calc_era5.py --startYear 1993 --endYear 2013
#python subset_calc_era5.py --startYear 1993 --endYear 2014
python subset_calc_era5.py --startYear 1993 --endYear 2015
python subset_calc_era5.py --startYear 1993 --endYear 2016
python subset_calc_era5.py --startYear 1993 --endYear 2017
python subset_calc_era5.py --startYear 1993 --endYear 2018
