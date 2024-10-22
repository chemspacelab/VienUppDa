#!/bin/bash

workdir=workdir

rm -Rf $workdir

int_script=internal_script.py

slot_file=slots.txt

if [ ! -f "$slot_file" ]
then
    echo "Define slots.txt"
    exit
fi

# The script that ends up being copied and executed.
cat > $int_script << EOF
from redox_database_gen.local_calc_schedule import schedule_local_bulk_calc
from redox_database_gen.molpro_calcs import TemplateCalculator
from redox_database_gen.utils import name_nodir
import os, subprocess, sys


static_kw_params={"MEMORY" : 5600, "INT_NAME" : "integrals.int"}

calculator=TemplateCalculator("../molpro_redox.com")

open_shell_methods={"CC_TYPE" : "uccsd", "MP2_TYPE" : "rmp2", "HF_TYPE" : "rhf"}

closed_shell_methods={"CC_TYPE" : "lccsd", "MP2_TYPE" : "mp2", "HF_TYPE" : "hf"}

charge_0_wfu="charge_0.wfu"
charge_1_wfu="charge_1.wfu"
charge_m1_wfu="charge_m1.wfu"

changed_kw_params_list=[{"CALC_TYPE_NAME" : "charge_0",
        "CHARGE" : 0,
        "SPIN" : 0,
        "WFU_NAME" : charge_0_wfu} | closed_shell_methods,
        {
        "CALC_TYPE_NAME" : "charge_1",
        "CHARGE" : 1,
        "SPIN" : 1,
        "WFU_NAME" : charge_1_wfu
        } | open_shell_methods,
        {
        "CALC_TYPE_NAME" : "charge_m1",
        "CHARGE" : -1,
        "SPIN" : 1,
        "WFU_NAME" : charge_m1_wfu,
        } | open_shell_methods,
        {
        "CALC_TYPE_NAME" : "CLEANUP",
        "TEMP_FILETYPES" : ["wfu", "int"]
        }
    ]

xyz_file_of_interest=name_nodir(sys.argv[1])

start_file=None
#start_file="./START" # the calculation will then wait for the START file to appear.



schedule_local_bulk_calc(xyz_file_of_interest, changed_kw_params_list, static_kw_params, calculator, nMPI_procs=12, nSlots=1,
                    killswitch_file="./EXIT", start_file=start_file, finish_file="./FINISHED", scheduler_time_delay=5, check_disk_usage=True, single_xyz=True)

EOF


# The script that stays on the initial machine and handles scheduling to other machines.
cat > external_script.py << EOF
from redox_database_gen.global_calc_schedule import schedule_global_bulk_calc
from redox_database_gen.remote_script_launch import RemoteLaunch
import glob

calculator=RemoteLaunch("$int_script", "$(pwd)/$workdir", additional_executable="python", dependency_files=["/home/konst/qmlcode/redox_database_gen/templates/molpro_redox_calc/molpro_redox.com"])

xyz_list=glob.glob("$(pwd)/$1/*.xyz")

schedule_global_bulk_calc(xyz_list, calculator, "$slot_file", scheduler_time_delay=10, killswitch_file="./EXIT", finish_file="./FINISHED", finalize_wait=10, raise_bad_slot_exception=False, default_nice_value=19)

EOF

python external_script.py > global_sched.stdout 2> global_sched.stderr &
