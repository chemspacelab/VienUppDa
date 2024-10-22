import os
import random
import time

from .base_classes import BadCalcSlotErr


def schedule_bulk_calc(
    param_iterator,
    calc_slots,
    calculator,
    scheduler_time_delay=0.5,
    killswitch_file=None,
    start_file=None,
    finish_file=None,
    slot_shuffle=False,
    raise_bad_slot_exception=True,
):
    go_on = True
    if start_file is not None:
        wait_for_file(start_file, scheduler_time_delay)
    finished_iterating = False
    while go_on:
        if slot_shuffle:
            random.shuffle(calc_slots)
        go_on = False
        killswitch_absent = file_absent(killswitch_file)
        for calc_slot in calc_slots:
            calc_slot.update_info()
            if raise_bad_slot_exception:
                if calc_slot.bad_slot:
                    raise BadCalcSlotErr
            if calc_slot.need_finalizing:
                calc_slot.finalize_calc()
            if not calc_slot.bad_slot:
                if calc_slot.unoccupied:
                    print("Occupying:", calc_slot)
                    if killswitch_absent:
                        calc_slot.reoccupy()
                        if calc_slot.stopped_iterating:
                            try:
                                static_kw_params = param_iterator.next()
                                calc_slot.occupy(calculator, **static_kw_params)
                                go_on = True
                            except StopIteration:
                                finished_iterating = True
                        else:
                            go_on = True
                else:
                    if not finished_iterating:
                        go_on = True
        time.sleep(scheduler_time_delay)
    if finish_file is not None:
        ffile = open(finish_file, "w")
        ffile.write("Finished.")
        ffile.close()


def wait_for_file(filename, scheduler_time_delay):
    while file_absent(filename):
        time.sleep(scheduler_time_delay)


def file_absent(filename):
    if filename is None:
        return True
    else:
        return not os.path.isfile(filename)
