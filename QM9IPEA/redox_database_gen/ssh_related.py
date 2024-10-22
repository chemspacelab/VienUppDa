import glob
import os
import subprocess

from .base_classes import BadCalcSlotErr

default_key_bits_size = 4096


def machine_address_check_user(machine_address):
    if "@" not in machine_address:
        return os.environ["USER"] + "@" + machine_address
    else:
        return machine_address


def exist_ssh_public_key():
    return len(glob.glob(os.path.expanduser("~") + "/.ssh/id_*.pub")) > 0


def create_ssh_public_key(other_machine=None):
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", str(default_key_bits_size)])


def copy_ssh_public_key(other_machine):
    subprocess.run(["ssh-copy-id", "-i", other_machine])


def configure_passwordless_access(machine_list):
    if not exist_ssh_public_key():
        create_ssh_public_key()
    for machine_address in machine_list:
        cur_machine_address = machine_address_check_user(machine_address)
        if not public_key_authentication_possible(cur_machine_address):
            copy_ssh_public_key(cur_machine_address)


def ssh_command_string(command_list, machine_name, ssh_flags=[]):
    total_command_list = ["ssh", "-tt"] + ssh_flags + [machine_name] + command_list
    return total_command_list


def get_remote_output(command_list, machine_name, ssh_flags=[], get_stderr=False):
    if isinstance(machine_name, str):
        command_str = ssh_command_string(command_list, machine_name, ssh_flags)
    else:
        command_str = ssh_command_string(command_list, machine_name[-1], ssh_flags)
        for mname in machine_name[: len(machine_name) - 1][::-1]:
            command_str = ssh_command_string(command_str, mname)
    if get_stderr:
        add_kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.PIPE}
    else:
        add_kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.DEVNULL}
    run_instance = subprocess.run(command_str, **add_kwargs, encoding="utf-8")
    if get_stderr:
        return run_instance.stderr
    else:
        return run_instance.stdout


def good_float(string_in):
    try:
        return float(string_in)
    except ValueError:
        return float(string_in.replace(",", "."))


def remote_execute(command_list, machine_name, ssh_flags=[]):
    return subprocess.run(ssh_command_string(command_list, machine_name, ssh_flags=ssh_flags))


def remotely_check_cpu_usage(machine_name, user=None):
    top_command = ["top", "-bn1"]
    if user is not None:
        top_command += ["-u", user]
    top_output = get_remote_output(top_command, machine_name)
    if top_output == "":  # the machine is down
        return None
    name_cpu_column = "%CPU"

    summed_id = None
    counted_cpu = 0.0

    for line in top_output.split("\n"):
        l_split = line.split()
        if summed_id is None:
            if name_cpu_column in l_split:
                summed_id = l_split.index(name_cpu_column)
        else:
            if l_split != []:
                counted_cpu += good_float(l_split[summed_id])
    return counted_cpu


def command_list2str(command_list):
    command_line = ""
    for command in command_list:
        command_line += command + " "
    return command_list


def public_key_authentication_possible(*machine_names):
    split_output = get_remote_output(
        ["exit"],
        machine_names,
        ssh_flags=["-vvv", "-o", "PasswordAuthentication=no", "-o", "BatchMode=yes"],
        get_stderr=True,
    ).split("\n")
    return "debug1: Authentication succeeded (publickey)." in split_output


def current_machine():
    return os.environ["USER"] + "@" + subprocess.check_output(["hostname"], encoding="utf-8")[:-1]


def name_nodir(name_in):
    return name_in.split("/")[-1]


def clone_dir_elsewhere(dir_full_path, other_machine, inverse=False):
    if inverse:
        source_prefix = other_machine + ":"
        destination_prefix = ""
    else:
        destination_prefix = other_machine + ":"
        source_prefix = ""
    run_instance = subprocess.run(
        ["rsync", "-Rr", source_prefix + dir_full_path, destination_prefix + "/"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    if run_instance.returncode != 0:
        raise BadCalcSlotErr
