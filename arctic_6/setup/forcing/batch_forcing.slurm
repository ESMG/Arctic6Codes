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

# run
cd /import/AKWATERS/jrcermakiii/src/Arctic6Codes/mid_12/setup/forcing
python subset_calc_era5.py
