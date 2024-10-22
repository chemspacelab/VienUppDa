import os
import subprocess

from redox_database_gen.local_calc_schedule import schedule_local_bulk_calc
from redox_database_gen.molpro_calcs import TemplateCalculator

static_kw_params = {"MEMORY": 5600, "INT_NAME": "integrals.int"}

calculator = TemplateCalculator("../../templates/molpro_redox_calc/molpro_redox.com")

open_shell_methods = {"CC_TYPE": "uccsd", "MP2_TYPE": "rmp2", "HF_TYPE": "rhf"}

closed_shell_methods = {"CC_TYPE": "lccsd", "MP2_TYPE": "mp2", "HF_TYPE": "hf"}

charge_0_wfu = "charge_0.wfu"
charge_1_wfu = "charge_1.wfu"
charge_m1_wfu = "charge_m1.wfu"

changed_kw_params_list = [
    {"CALC_TYPE_NAME": "charge_0", "CHARGE": 0, "SPIN": 0, "WFU_NAME": charge_0_wfu}
    | closed_shell_methods,
    {
        "CALC_TYPE_NAME": "charge_1",
        "CHARGE": 1,
        "SPIN": 1,
        "WFU_NAME": charge_1_wfu,
        "DEPENDS": [[charge_0_wfu, charge_1_wfu]],
    }
    | open_shell_methods,
    {
        "CALC_TYPE_NAME": "charge_m1",
        "CHARGE": -1,
        "SPIN": 1,
        "WFU_NAME": charge_m1_wfu,
        "DEPENDS": [[charge_0_wfu, charge_m1_wfu]],
    }
    | open_shell_methods,
    {"CALC_TYPE_NAME": "CLEANUP", "TEMP_FILETYPES": ["wfu", "int"]},
]

MYDIR = os.getcwd()

# tar_partition=MYDIR+'/methane_xyz.tar'
tar_partition = MYDIR + "/partitioned_qm7_xyzs/partitioned_qm7_xyzs_0.tar"

workdir = MYDIR + "/workdir"

subprocess.run(["mkdir", "-p", workdir])

os.chdir(workdir)

start_file = None
# start_file="./START" # the calculation will then wait for the START file to appear.

schedule_local_bulk_calc(
    tar_partition,
    changed_kw_params_list,
    static_kw_params,
    calculator,
    nMPI_procs=14,
    nSlots=3,
    killswitch_file="./EXIT",
    start_file=start_file,
    finish_file="./FINISHED",
    scheduler_time_delay=10,
    check_disk_usage=True,
)
