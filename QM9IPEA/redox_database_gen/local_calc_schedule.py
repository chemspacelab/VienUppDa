import os
import subprocess
import tarfile

from .base_classes import CalcSlot
from .partition_calc_schedule import schedule_bulk_calc
from .utils import (
    check_create_randomized_list,
    default_if_key_absent,
    str_no_special_chars,
    tar_read_geom_lines,
    timechecked_Popen,
    xyzfile2geom,
)


def schedule_local_bulk_calc(
    tar_file,
    changed_kw_params_list,
    default_kw_params,
    calculator,
    nMPI_procs=None,
    nOMP_threads=None,
    nSlots=1,
    compression=None,
    scheduler_time_delay=0.5,
    cpu_hist_step=10.0,
    mem_hist_step=4194304,
    disk_hist_step=1048576,
    killswitch_file=None,
    start_file=None,
    finish_file=None,
    check_disk_usage=False,
    randomized_list_dump="randomized_list.pkl",
    scratch_dir="scratch",
    single_xyz=False,
    raise_bad_slot_exception=True,
):
    calc_slots = [
        LocalCalcSlot(
            nMPI_procs=nMPI_procs,
            nOMP_threads=nOMP_threads,
            cpu_hist_step=cpu_hist_step,
            mem_hist_step=mem_hist_step,
            scratch_dir=scratch_dir,
            check_disk_usage=check_disk_usage,
            disk_hist_step=disk_hist_step,
        )
        for slot_counter in range(nSlots)
    ]
    if single_xyz:
        param_iterator = LocalXYZIterator(tar_file, changed_kw_params_list, default_kw_params)
    else:
        param_iterator = LocalTarIterator(
            tar_file,
            changed_kw_params_list,
            default_kw_params,
            compression=compression,
            randomized_list_dump=randomized_list_dump,
        )

    schedule_bulk_calc(
        param_iterator,
        calc_slots,
        calculator,
        scheduler_time_delay=scheduler_time_delay,
        killswitch_file=killswitch_file,
        start_file=start_file,
        finish_file=finish_file,
        raise_bad_slot_exception=raise_bad_slot_exception,
    )


class LocalTarIterator:
    def __init__(
        self,
        tar_file,
        changed_kw_params_list,
        default_kw_params,
        compression=None,
        randomized_list_dump="randomized_list.pkl",
    ):
        self.tar_file = tarfile.open(tar_file, "r")
        randomized_list = check_create_randomized_list(
            self.tar_file.getnames(), randomized_list_dump
        )
        self.actual_iterator = iter(randomized_list)
        self.default_kw_params = default_kw_params
        self.changed_kw_params_list = changed_kw_params_list

    def next(self):
        cur_xyz_name = next(self.actual_iterator)
        return self.default_kw_params | {
            "GEOM_LINES": tar_read_geom_lines(self.tar_file, cur_xyz_name),
            "JOB_NAME": str_no_special_chars(cur_xyz_name),
            "changed_kw_params_list": self.changed_kw_params_list,
        }


# Not really needed?
class LocalXYZIterator:
    def __init__(self, xyz_file, changed_kw_params_list, default_kw_params):
        self.actual_iterator = iter([xyz_file])
        self.default_kw_params = default_kw_params
        self.changed_kw_params_list = changed_kw_params_list

    def next(self):
        cur_xyz_name = next(self.actual_iterator)
        return self.default_kw_params | {
            "GEOM_LINES": xyzfile2geom(cur_xyz_name),
            "JOB_NAME": str_no_special_chars(cur_xyz_name),
            "changed_kw_params_list": self.changed_kw_params_list,
        }


class LocalCalcSlot(CalcSlot):
    def __init__(
        self,
        cpu_hist_step=10.0,
        mem_hist_step=4194304,
        disk_hist_step=1048576,
        final_info_suffix="final_info",
        nMPI_procs=None,
        nOMP_threads=None,
        scratch_dir="scratch",
        check_disk_usage=False,
    ):
        super().__init__()

        self.cpu_hist = []
        self.max_cpu_usage = None
        self.cpu_hist_step = cpu_hist_step

        self.mem_hist_rss = []
        self.mem_hist_vsz = []

        self.max_mem_usage_rss = None
        self.max_mem_usage_vsz = None

        self.mem_hist_step = mem_hist_step

        self.mydir = None

        self.final_info_suffix = final_info_suffix
        self.job_name = None
        self.calc_name = None

        self.nMPI_procs = nMPI_procs
        self.nOMP_threads = nOMP_threads

        self.scratch_dir = scratch_dir

        self.workdir = None

        self.check_disk_usage = check_disk_usage
        if self.check_disk_usage:
            self.disk_hist = []
            self.disk_hist_step = disk_hist_step
            self.max_disk_usage = None

    def occupy(self, calculator, changed_kw_params_list=None, **static_kw_params):
        self.calculator = calculator
        self.mydir = os.getcwd()
        self.job_name = static_kw_params["JOB_NAME"]
        self.workdir = self.mydir + "/" + self.job_name
        self.scratch_dir_full = self.mydir + "/" + self.scratch_dir + "/" + self.job_name
        for directory in [self.workdir, self.scratch_dir_full]:
            subprocess.run(["mkdir", "-p", directory])
        self.param_iterator = iter(changed_kw_params_list)
        self.static_kw_params = static_kw_params
        self.stopped_iterating = False
        self.reoccupy()

    def reoccupy(self):
        if self.stopped_iterating:
            return
        try:
            changed_kw_params = next(self.param_iterator)
        except StopIteration:
            self.stopped_iterating = True
            return
        self.mydir = os.getcwd()
        os.chdir(self.workdir)
        self.calc_name = (
            self.static_kw_params["JOB_NAME"] + "_" + changed_kw_params["CALC_TYPE_NAME"]
        )
        all_kw_params = changed_kw_params | self.static_kw_params | {"CALC_NAME": self.calc_name}
        if all_kw_params["CALC_TYPE_NAME"] == "CLEANUP":
            self.popen = self.cleanup_proc(**all_kw_params)
        else:
            self.popen = self.calculator.make_calc(
                **all_kw_params,
                NMPI_PROCS=self.nMPI_procs,
                NOMP_THREADS=self.nOMP_threads,
                FULL_WORKDIR=self.workdir,
                SCRATCH_DIR=self.scratch_dir_full
            )
        os.chdir(self.mydir)
        self.unoccupied = self.popen is None

    def update_additional_info(self):
        cur_cpu_usage, cur_mem_usage_rss, cur_mem_usage_vsz = count_children_cpu_mem_usage(
            self.popen.pid
        )

        self.max_cpu_usage = ext_max(self.max_cpu_usage, cur_cpu_usage)
        self.max_mem_usage_rss = ext_max(self.max_mem_usage_rss, cur_mem_usage_rss)
        self.max_mem_usage_vsz = ext_max(self.max_mem_usage_vsz, cur_mem_usage_vsz)
        update_histogram(self.cpu_hist, self.cpu_hist_step, cur_cpu_usage)
        update_histogram(self.mem_hist_rss, self.mem_hist_step, cur_mem_usage_rss)
        update_histogram(self.mem_hist_vsz, self.mem_hist_step, cur_mem_usage_vsz)

        if self.check_disk_usage:
            cur_disk_usage = directory_size(self.scratch_dir_full)
            self.max_disk_usage = ext_max(self.max_disk_usage, cur_disk_usage)
            update_histogram(self.disk_hist, self.disk_hist_step, cur_disk_usage)

    def additional_finalize_calc(self, final_info_suffix="cpu_mem_logs"):
        final_info_name = self.calc_name + "." + final_info_suffix
        os.chdir(self.workdir)
        output = open(final_info_name, "w")
        dump_histogram(self.cpu_hist, self.cpu_hist_step, "%CPU", output)
        dump_histogram(self.mem_hist_rss, self.mem_hist_step, "RSS", output)
        dump_histogram(self.mem_hist_vsz, self.mem_hist_step, "VSZ", output)
        if self.check_disk_usage:
            dump_histogram(self.disk_hist, self.mem_hist_step, "DISK_USAGE", output)
        print("MAX %CPU:", self.max_cpu_usage, file=output)
        print("MAX RSS:", self.max_mem_usage_rss, file=output)
        print("MAX VSZ:", self.max_mem_usage_vsz, file=output)
        if self.check_disk_usage:
            print("MAX DISK_USAGE:", self.max_disk_usage, file=output)
        output.close()
        os.chdir(self.mydir)

    def cleanup_proc(self, **kwargs):
        tmpfile_types = default_if_key_absent(kwargs, "TEMP_FILETYPES")
        if tmpfile_types is None:
            return None
        else:
            commands = ["rm", "-f"]
            for tmpfile_type in tmpfile_types:
                commands += ["*." + tmpfile_type]
            return timechecked_Popen(
                commands,
                script_name="molpro_" + kwargs["CALC_NAME"] + ".sh",
                time_log_output=kwargs["CALC_NAME"] + ".timestamps",
            )


def dump_histogram(histogram, histogram_step, hist_name, output_file):
    print("BEGIN", hist_name, "STEP", histogram_step, file=output_file)
    for val in histogram:
        print(val, file=output_file)
    print("END", hist_name, file=output_file)


def ext_max(val1, val2):
    if val1 is None:
        return val2
    else:
        return max(val1, val2)


def directory_size(dir_path):
    try:
        return float(
            subprocess.check_output(["du", dir_path], encoding="utf-8")
            .split("\n")[-2]
            .split("\t")[0]
        )
    except subprocess.CalledProcessError:
        return 0.0


def count_children_cpu_mem_usage(parent_process_id):
    all_pids = [parent_process_id]
    current_check = 0
    while current_check != len(all_pids):
        try:
            all_pids += [
                int(pid_str)
                for pid_str in subprocess.check_output(
                    ["pgrep", "-P", str(all_pids[current_check])], encoding="utf-8"
                ).split()
            ]
        except subprocess.CalledProcessError:
            pass
        current_check += 1
    cur_cpu = 0.0
    cur_mem_rss = 0.0
    cur_mem_vsz = 0.0
    for pid in all_pids:
        try:
            cpu_mem_line = subprocess.check_output(
                ["ps", "-o", "%cpu,rss,vsz", "-p" + str(pid)], encoding="utf-8"
            ).split("\n")[1]
            cml_spl = cpu_mem_line.split()
            cur_cpu += float(cml_spl[0])
            cur_mem_rss += int(cml_spl[1])
            cur_mem_vsz += int(cml_spl[2])
        except subprocess.CalledProcessError:
            pass
    return cur_cpu, cur_mem_rss, cur_mem_vsz


def update_histogram(histogram, histogram_step, val):
    hist_id = int(val / histogram_step)
    if hist_id >= len(histogram):
        added_zeros = hist_id - len(histogram) + 1
        for counter in range(added_zeros):
            histogram.append(0)
    histogram[hist_id] += 1
