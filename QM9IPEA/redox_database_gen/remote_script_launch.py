import subprocess

from .ssh_related import clone_dir_elsewhere, current_machine, remote_execute, ssh_command_string
from .utils import check_full_path, generate_timechecked_script, name_nodir, str_no_special_chars


class RemoteLaunch:
    def __init__(self, launched_script, workdir, additional_executable=None, dependency_files=[]):
        self.launched_script = check_full_path(launched_script)
        self.workdir = check_full_path(workdir)
        self.additional_executable = additional_executable

        subprocess.run(self.make_workdir())
        self.to_synchronize = []

        for dep_file in [*dependency_files, launched_script]:
            subprocess.run(["cp", "-f", dep_file, self.workdir])
            self.to_synchronize.append(name_nodir(dep_file))
        # Generate scripts that will actually be executed.
        infile_commands = ["nice", "-n$3"]
        if self.additional_executable is not None:
            infile_commands += [self.additional_executable]
        infile_commands += ["../" + name_nodir(self.launched_script), "$1"]
        exec_name = "executor_" + name_nodir(self.launched_script) + ".sh"
        self.to_synchronize.append(exec_name)
        self.executor_name = self.workdir + "/" + exec_name
        generate_timechecked_script(
            infile_commands,
            script_name=self.executor_name,
            include_bashrc=True,
            rundir="$2",
        )

    def calc_slot_prepared(self, machine_address):
        if machine_address != current_machine():
            remote_execute(self.make_workdir(), machine_address)
            for sync_file in self.to_synchronize:
                clone_dir_elsewhere(self.workdir + "/" + sync_file, machine_address)

    def make_workdir(self):
        return ["mkdir", "-p", self.workdir]

    def make_calc(self, machine_address, **kwargs):
        filename = kwargs["FILENAME"]
        jobname = str_no_special_chars(name_nodir(filename))
        self.jobdir_full = self.workdir + "/" + jobname
        subprocess.run(["mkdir", "-p", self.jobdir_full])
        subprocess.run(["cp", "-f", filename, self.jobdir_full])

        executed_commands = [
            self.executor_name,
            filename,
            self.jobdir_full,
            str(kwargs["NICE_VALUE"]),
        ]
        if machine_address != current_machine():
            # scp everything to the remote machine.
            clone_dir_elsewhere(self.jobdir_full, machine_address)
            # SSH'd command
            executed_commands = ssh_command_string(executed_commands, machine_address)
        return subprocess.Popen(executed_commands)
