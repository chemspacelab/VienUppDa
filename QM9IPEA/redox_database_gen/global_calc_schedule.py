import subprocess
import time

from .base_classes import BadCalcSlotErr, CalcSlot
from .partition_calc_schedule import schedule_bulk_calc
from .ssh_related import (
    clone_dir_elsewhere,
    current_machine,
    machine_address_check_user,
    public_key_authentication_possible,
    remote_execute,
    remotely_check_cpu_usage,
)
from .utils import check_create_randomized_list

#   Do we need it?
# class PublicKeyAuthErr(Exception):
#    pass


def schedule_global_bulk_calc(
    input_file_list,
    calculator,
    slots_file,
    scheduler_time_delay=60,
    killswitch_file=None,
    start_file=None,
    finish_file=None,
    finalize_wait=None,
    objects_to_delete=None,
    default_nice_value=0,
    raise_bad_slot_exception=False,
):
    calc_slots = global_calc_slots_from_file(
        slots_file,
        calculator,
        finalize_wait=finalize_wait,
        objects_to_delete=objects_to_delete,
        default_nice_value=default_nice_value,
    )
    param_iterator = Processed_file_iterator(input_file_list)
    schedule_bulk_calc(
        param_iterator,
        calc_slots,
        calculator,
        scheduler_time_delay=scheduler_time_delay,
        killswitch_file=killswitch_file,
        start_file=start_file,
        finish_file=finish_file,
        slot_shuffle=True,
        raise_bad_slot_exception=raise_bad_slot_exception,
    )


def global_calc_slots_from_file(
    slots_file,
    calculator,
    finalize_wait=None,
    objects_to_delete=None,
    default_nice_value=0,
):
    output = []
    with open(slots_file, "r") as f:
        for line in f.readlines():
            splline = line.split()
            machine_address = machine_address_check_user(splline[0])
            slot_number = int(splline[1])
            total_cpu_occ_sub_cond = int(splline[2])
            if len(splline) > 3:
                cur_nice_value = int(splline[3])
            else:
                cur_nice_value = default_nice_value
            try:
                calculator.calc_slot_prepared(machine_address)
                for i in range(slot_number):
                    new_slot = GlobalCalcSlot(
                        machine_address=machine_address,
                        total_cpu_occ_sub_cond=total_cpu_occ_sub_cond,
                        finalize_wait=finalize_wait,
                        objects_to_delete=objects_to_delete,
                        nice_value=cur_nice_value,
                    )
                    output.append(new_slot)
            except BadCalcSlotErr:
                print("Bad slot:", machine_address)
                continue
    return output


class Processed_file_iterator:
    def __init__(self, processed_file_list, randomized_list_dump="randomized_list.pkl"):
        randomized_list = check_create_randomized_list(processed_file_list, randomized_list_dump)
        self.actual_iterator = iter(randomized_list)

    def next(self):
        filename = next(self.actual_iterator)
        return {"FILENAME": filename, "JOBDIR": "."}


class GlobalCalcSlot(CalcSlot):
    def __init__(
        self,
        machine_address=None,
        total_cpu_occ_sub_cond=None,
        finalize_wait=None,
        objects_to_delete=None,
        nice_value=0,
    ):
        super().__init__()

        self.machine_address = machine_address
        self.total_cpu_occ_sub_cond = total_cpu_occ_sub_cond
        # Check that public key authentication is possible.
        if not public_key_authentication_possible(machine_address):
            self.make_bad_slot()

        self.update_info()  # first of all, check whether the machine is currently occupied.
        self.jobdir_full = None

        self.finalize_wait = finalize_wait
        self.objects_to_delete = objects_to_delete

        self.nice_value = nice_value

    def occupy(self, calculator, **kwargs):
        self.popen = calculator.make_calc(
            self.machine_address, NICE_VALUE=self.nice_value, **kwargs
        )
        self.jobdir_full = calculator.jobdir_full
        self.unoccupied = False

    def reoccupy(self):
        pass

    def additional_finalize_calc(self, final_info_suffix="cpu_mem_logs"):
        if self.finalize_wait is not None:
            time.sleep(self.finalize_wait)
        delete_objects(self.objects_to_delete, self.machine_address, self.jobdir_full)
        if self.machine_address != current_machine():
            try:
                clone_dir_elsewhere(self.jobdir_full, self.machine_address, inverse=True)
            except BadCalcSlotErr:
                self.make_bad_slot()

    def cleanup_proc(self, **kwargs):
        pass

    def make_bad_slot(self):
        self.bad_slot = True
        print("Bad slot:", self.machine_address)

    def additional_check_unoccupied(self):
        cpu_usage_check = remotely_check_cpu_usage(self.machine_address)
        if cpu_usage_check is None:
            self.make_bad_slot()
            self.unoccupied = False
        else:
            self.unoccupied = cpu_usage_check < self.total_cpu_occ_sub_cond

    def __str__(self):
        return (
            "Slot address:"
            + self.machine_address
            + ",CPU usage limit:"
            + str(self.total_cpu_occ_sub_cond)
            + ",vacant:"
            + str(self.unoccupied)
        )

    def __repr__(self):
        return str(self)


def delete_objects(objects_to_delete, machine_address, workdir):
    if objects_to_delete is not None:
        for obj in objects_to_delete:
            delete_command = ["rm", "-Rf", workdir + "/" + obj]
            try:
                if machine_address == current_machine():
                    subprocess.run(delete_command)
                else:
                    remote_execute(delete_command, machine_address)
            except subprocess.CalledProcessError:
                pass
