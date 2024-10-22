class CalcSlot:
    def __init__(self):
        self.popen = None
        self.unoccupied = True  # Though may need to double check in update_info.
        self.need_finalizing = False
        self.stopped_iterating = True

        self.bad_slot = False

    def occupy(self, calculator, *args, **kwargs):
        pass

    def reoccupy(self):
        pass

    def update_info(self):
        if self.popen is None:
            self.additional_check_unoccupied()
            return
        else:
            return_code = self.popen.poll()
            self.need_finalizing = return_code is not None
            if self.need_finalizing:
                self.additional_check_unoccupied()
                self.bad_slot = return_code != 0
                return
        self.update_additional_info()

    def additional_check_unoccupied(self):
        self.unoccupied = True  # by default there are no additional conditions.

    def update_additional_info(self):
        pass

    def finalize_calc(self, final_info_suffix="cpu_mem_logs"):
        if self.popen is None:  # was not initialized
            return
        self.popen = None
        self.need_finalizing = False
        self.additional_finalize_calc()

    def additional_finalize_calc(self):
        pass


class BadCalcSlotErr(Exception):
    pass
