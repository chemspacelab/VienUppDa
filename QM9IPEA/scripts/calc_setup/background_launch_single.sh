#!/bin/bash

tar_name=$1

if [ "$tar_name" == "" ]
then
    exit
fi

tar_name=$(pwd)/$tar_name

workdir=$(echo $tar_name | rev | cut -d'.' -f2- | rev)_workdir

mkdir $workdir

cd $workdir

TEMPLATE="/home/konst/qmlcode/redox_database_gen/templates/molpro_redox_calc/molpro_redox.com"

cat > python_script.py << EOF
from redox_database_gen.partition_calc_schedule import schedule_bulk_calc
from redox_database_gen.molpro_calcs import Template_calculator
import os, subprocess, sys

static_kw_params={"MEMORY" : 4500, "INT_NAME" : "integrals.int"}

calculator=Template_calculator("$TEMPLATE")

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
        "WFU_NAME" : charge_1_wfu,
        "DEPENDS" : [[charge_0_wfu, charge_1_wfu]]
        } | open_shell_methods,
        {
        "CALC_TYPE_NAME" : "charge_m1",
        "CHARGE" : -1,
        "SPIN" : 1,
        "WFU_NAME" : charge_m1_wfu,
        "DEPENDS" : [[charge_0_wfu, charge_m1_wfu]]
        } | open_shell_methods,
        {
        "CALC_TYPE_NAME" : "CLEANUP",
        "TEMP_FILETYPES" : ["wfu", "int"]
        }
    ]

MYDIR=os.getcwd()

tar_partition=sys.argv[1]

start_file=None
#start_file="./START" # the calculation will then wait for the START file to appear.

schedule_bulk_calc(tar_partition, changed_kw_params_list, static_kw_params, calculator, nMPI_procs=6, nSlots=4,
    killswitch_file="./EXIT", start_file=start_file, finish_file="./FINISHED", scheduler_time_delay=5, check_disk_usage=True)

EOF

output="./output"
mkdir -p $output
cd $output
python ../python_script.py $tar_name > ../stdout.log 2> ../stderr.log &
