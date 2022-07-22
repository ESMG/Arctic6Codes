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

ulimit -u 25000
ulimit -n 2048

conda activate gridTools

cd /import/AKWATERS/jrcermakiii/configs/Arctic12/OBC/obc_gen

python ../combine_year.py --doYear 1993 --srcDir p1993 --dstDir 1993 --fixStartTime True
python ../combine_year.py --doYear 1994 --srcDir p1994 --dstDir 1994 --pad 1993,1994
python ../combine_year.py --doYear 1995 --srcDir p1995 --dstDir 1995 --pad 1994,1995
python ../combine_year.py --doYear 1996 --srcDir p1996 --dstDir 1996 --pad 1995,1996
python ../combine_year.py --doYear 1997 --srcDir p1997 --dstDir 1997 --pad 1996,1997
python ../combine_year.py --doYear 1998 --srcDir p1998 --dstDir 1998 --pad 1997,1998
python ../combine_year.py --doYear 1999 --srcDir p1999 --dstDir 1999 --pad 1998,1999
# Preparing
#python ../combine_year.py --doYear 2000 --srcDir p2000 --dstDir 2000 --pad 1999,2000
#python ../combine_year.py --doYear 2001 --srcDir p2001 --dstDir 2001 --pad 2000,2001
#python ../combine_year.py --doYear 2002 --srcDir p2002 --dstDir 2002 --pad 2001,2002
#python ../combine_year.py --doYear 2003 --srcDir p2003 --dstDir 2003 --pad 2002,2003
#python ../combine_year.py --doYear 2004 --srcDir p2004 --dstDir 2004 --pad 2003,2004
#python ../combine_year.py --doYear 2005 --srcDir p2005 --dstDir 2005 --pad 2004,2005
#python ../combine_year.py --doYear 2006 --srcDir p2006 --dstDir 2006 --pad 2005,2006
#python ../combine_year.py --doYear 2007 --srcDir p2007 --dstDir 2007 --pad 2006,2007
#python ../combine_year.py --doYear 2008 --srcDir p2008 --dstDir 2008 --pad 2007,2008
#python ../combine_year.py --doYear 2009 --srcDir p2009 --dstDir 2009 --pad 2008,2009
#python ../combine_year.py --doYear 2010 --srcDir p2010 --dstDir 2010 --pad 2009,2010

# Fix permissions
chmod ug+r ????/*.nc
