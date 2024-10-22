#!/bin/bash

ELEMENTS=("C" "N" "O" "F") # "H" not included because it crashes MP2 or CC calculations.

declare -A SPINS=( ["H"]="1" ["C"]="2" ["N"]="3" ["O"]="2" ["F"]="1")

MYDIR=$(pwd)

WDIR=atom_ens

mkdir $WDIR
cd $WDIR

for EL in ${ELEMENTS[@]}
do
    mkdir $EL
    cd $EL
    SPIN=${SPINS[$EL]}
    int_script=internal_script.py

    XYZ_NAME=$EL.xyz

    cat > $XYZ_NAME << EOF
1

$EL 0.0 0.0 0.0
EOF

    # The script that ends up being copied and executed.
    cat > $int_script << EOF
from redox_database_gen.local_calc_schedule import schedule_local_bulk_calc
from redox_database_gen.molpro_calcs import TemplateCalculator
from redox_database_gen.utils import name_nodir
import os, sys

static_kw_params={"MEMORY" : 5600, "INT_NAME" : "integrals.int"}

calculator=TemplateCalculator("$MYDIR/../../templates/molpro_redox_calc/molpro_redox.com")

open_shell_methods={"CC_TYPE" : "uccsd", "MP2_TYPE" : "rmp2", "HF_TYPE" : "rhf"}

changed_kw_params_list=[{"CALC_TYPE_NAME" : "atom_en",
        "CHARGE" : 0,
        "SPIN" : $SPIN,
        "WFU_NAME" : "wfu"} | open_shell_methods
    ]

xyz_file_of_interest=name_nodir(sys.argv[1])

start_file=None
#start_file="./START" # the calculation will then wait for the START file to appear.



schedule_local_bulk_calc(xyz_file_of_interest, changed_kw_params_list, static_kw_params, calculator, nMPI_procs=6, nSlots=1,
                    killswitch_file="./EXIT", start_file=start_file, finish_file="./FINISHED", scheduler_time_delay=5, check_disk_usage=True, single_xyz=True)

EOF
    python $int_script $XYZ_NAME
    cd ..

done
