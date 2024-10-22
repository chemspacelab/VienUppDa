import sys

from redox_database_gen.local_calc_schedule import schedule_local_bulk_calc
from redox_database_gen.molpro_calcs import TemplateCalculator
from redox_database_gen.utils import name_nodir

# MEMORY=5600
MEMORY = 200

# nMPI_procs=12
nMPI_procs = 1

static_kw_params = {"MEMORY": MEMORY, "INT_NAME": "integrals.int"}


calculator = TemplateCalculator("molpro_redox.com")

open_shell_methods = {"CC_TYPE": "uccsd", "MP2_TYPE": "rmp2", "HF_TYPE": "rhf"}

closed_shell_methods = {"CC_TYPE": "lccsd", "MP2_TYPE": "mp2", "HF_TYPE": "hf"}

charge_0_wfu = "charge_0.wfu"
charge_1_wfu = "charge_1.wfu"
charge_m1_wfu = "charge_m1.wfu"

# If you want to reuse charge=0 MO's as initial guess for charge=1 and charge=-1.
DEPENDS_charge_1 = [[charge_0_wfu, charge_1_wfu]]
DEPENDS_charge_m1 = [[charge_0_wfu, charge_m1_wfu]]
# DEPENDS_charge_1=[]
# DEPENDS_charge_m1=[]

changed_kw_params_list = [
    {"CALC_TYPE_NAME": "charge_0", "CHARGE": 0, "SPIN": 0, "WFU_NAME": charge_0_wfu}
    | closed_shell_methods,
    {
        "CALC_TYPE_NAME": "charge_1",
        "CHARGE": 1,
        "SPIN": 1,
        "WFU_NAME": charge_1_wfu,
        "DEPENDS": DEPENDS_charge_1,
    }
    | open_shell_methods,
    {
        "CALC_TYPE_NAME": "charge_m1",
        "CHARGE": -1,
        "SPIN": 1,
        "WFU_NAME": charge_m1_wfu,
        "DEPENDS": DEPENDS_charge_m1,
    }
    | open_shell_methods,
    {"CALC_TYPE_NAME": "CLEANUP", "TEMP_FILETYPES": ["wfu", "int"]},
]

xyz_file_of_interest = name_nodir(sys.argv[1])

start_file = None
# start_file="./START" # the calculation will then wait for the START file to appear.


schedule_local_bulk_calc(
    xyz_file_of_interest,
    changed_kw_params_list,
    static_kw_params,
    calculator,
    nMPI_procs=nMPI_procs,
    nSlots=1,
    killswitch_file="./EXIT",
    start_file=start_file,
    finish_file="./FINISHED",
    scheduler_time_delay=5,
    check_disk_usage=True,
    single_xyz=True,
)
