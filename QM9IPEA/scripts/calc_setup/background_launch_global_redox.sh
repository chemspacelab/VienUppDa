#!/bin/bash

workdir=workdir

#rm -Rf $workdir

rm -f randomized_list.pkl

int_script=internal_script.py

slot_file=slots.txt

if [ ! -f "$slot_file" ]
then
    echo "Define slots.txt"
    exit
fi

if [ "$1" == "" ]
then
    echo "Define xyz directory."
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

# If you want to reuse charge=0 MO's as initial guess for charge=1 and charge=-1.
DEPENDS_charge_1=[[charge_0_wfu, charge_1_wfu]]
DEPENDS_charge_m1=[[charge_0_wfu, charge_m1_wfu]]
#DEPENDS_charge_1=[]
#DEPENDS_charge_m1=[]

changed_kw_params_list=[{"CALC_TYPE_NAME" : "charge_0",
        "CHARGE" : 0,
        "SPIN" : 0,
        "WFU_NAME" : charge_0_wfu} | closed_shell_methods,
        {
        "CALC_TYPE_NAME" : "charge_1",
        "CHARGE" : 1,
        "SPIN" : 1,
        "WFU_NAME" : charge_1_wfu,
        "DEPENDS" : DEPENDS_charge_1
        } | open_shell_methods,
        {
        "CALC_TYPE_NAME" : "charge_m1",
        "CHARGE" : -1,
        "SPIN" : 1,
        "WFU_NAME" : charge_m1_wfu,
        "DEPENDS" : DEPENDS_charge_m1
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
                killswitch_file="./EXIT", start_file=start_file, finish_file="./FINISHED", scheduler_time_delay=5,
		check_disk_usage=True, single_xyz=True)

EOF


# The script that stays on the initial machine and handles scheduling to other machines.
cat > external_script.py << EOF
from redox_database_gen.global_calc_schedule import schedule_global_bulk_calc
from redox_database_gen.remote_script_launch import RemoteLaunch
import glob, os
from redox_database_gen.utils import str_no_special_chars, name_nodir

workdir="$(pwd)/$workdir"

calculator=RemoteLaunch("$int_script", workdir, additional_executable="python", dependency_files=["/home/konst/qmlcode/redox_database_gen/templates/molpro_redox_calc/molpro_redox.com"])

full_xyz_list=glob.glob("$(pwd)/$1/*.xyz")

xyz_list=[]

for xyz_name in full_xyz_list:
    if not os.path.isdir(workdir+"/"+str_no_special_chars(name_nodir(xyz_name))):
        xyz_list.append(xyz_name)

schedule_global_bulk_calc(xyz_list, calculator, "$slot_file", scheduler_time_delay=10, killswitch_file="./EXIT", finish_file="./FINISHED", finalize_wait=10, raise_bad_slot_exception=False, default_nice_value=19)

EOF

python external_script.py > global_sched.stdout 2> global_sched.stderr &
