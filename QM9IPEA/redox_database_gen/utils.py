import glob
import os
import pickle
import subprocess


def default_if_key_absent(dictionary, keyword, default_val=None, replace_None=True):
    try:
        val = dictionary[keyword]
        if replace_None:
            if val is None:
                return default_val
        return val
    except KeyError:
        return default_val


def name_nodir(filename):
    return filename.split("/")[-1]


def timechecked_Popen(commands, script_name=None, **other_kwargs):
    generate_timechecked_script(commands, script_name=script_name, **other_kwargs)
    return subprocess.Popen(["./" + script_name])


def date_call(time_log_output, overwrite):
    if overwrite:
        redirect = ">"
    else:
        redirect = ">>"
    return "echo $(date; hostname) " + redirect + " " + time_log_output


def mktemp(template="XXXXXXX", pdir="."):
    return subprocess.check_output(
        ["mktemp", "-p", pdir, "-t", template], encoding="utf-8"
    ).rstrip("\n")


def generate_timechecked_script(
    commands,
    script_name=None,
    time_log_output=None,
    dependencies=[],
    rundir=None,
    include_bashrc=False,
    nthreads_limit=None,
):
    if script_name is None:
        script_name = mktemp(template="XXXXXXX.sh", pdir=".")
    sh_file = open(script_name, "w")
    print("#!/bin/bash", file=sh_file)
    if include_bashrc:
        bashrc2file(sh_file)
    if nthreads_limit is not None:
        for var in [
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "NUMBA_NUM_THREADS",
        ]:
            print("export", var + "=" + nthreads_limit, file=sh_file)
    if rundir is not None:
        print("cd", rundir, file=sh_file)
    for dependency in dependencies:
        print("cp -f " + dependency[0] + " " + dependency[1], file=sh_file)
    if time_log_output is not None:
        print(date_call(time_log_output, True), file=sh_file)
    command_line = ""
    for command in commands:
        command_line += command + " "
    print(
        command_line,
        " > ",
        name_nodir(script_name) + ".stdout",
        " 2> ",
        name_nodir(script_name) + ".stderr",
        file=sh_file,
    )
    if time_log_output is not None:
        print(date_call(time_log_output, False), file=sh_file)
    sh_file.close()
    subprocess.run(["chmod", "+x", script_name])


def bashrc2file(sh_file):
    bashrc_lines = open(os.path.expanduser("~") + "/.bashrc", "r").readlines()
    for line in bashrc_lines:
        sh_file.write(line.replace("$-", "i"))
    print("\n", file=sh_file)


def num_omp_procs():
    try:
        return int(os.environ["OMP_NUM_THREADS"])
    except LookupError:
        return 1


# Ordered list of xyzs in a directory.
def dirs_xyz_list(QM9_dir):
    output = glob.glob(QM9_dir + "/*.xyz")
    output.sort()
    return output


def mktmpdir(dirname="."):
    return subprocess.check_output(["mktemp", "-d", "-p", dirname], text=True).rstrip("\n")


# Divides a list of xyzs into parts with and without dissociated molecules.
def rdkit_reasonable_molecules(xyz_list):
    from joblib import Parallel, delayed
    from mosaics.xyz2graph import xyz2mol_extgraph

    reasonable_mol_vals = Parallel(n_jobs=num_omp_procs(), backend="multiprocessing")(
        delayed(reasonable_molecule)(xyz_name, xyz2mol_extgraph) for xyz_name in xyz_list
    )
    final_xyz_list = []
    rejected_xyz_list = []
    for xyz_name, reasonable_mol in zip(xyz_list, reasonable_mol_vals):
        if reasonable_mol:
            final_xyz_list.append(xyz_name)
        else:
            rejected_xyz_list.append(xyz_name)
    return final_xyz_list, rejected_xyz_list


def reasonable_molecule(xyz_name, graph_func):
    cur_graph = graph_func(xyz_name)
    if cur_graph is None:
        return False
    return cur_graph.is_connected()


def insert_kwargs(string, **kw_params):
    output = string
    for kw in kw_params:
        if kw_params[kw] is not None:
            output = output.replace("$${" + kw + "}", str(kw_params[kw]))
    return output


def tar_read_geom_lines(tar_file, xyz_file):
    xyz_lines = tar_readlines(tar_file, xyz_file)
    return xyzlines2geom(xyz_lines)


def xyzlines2geom(xyz_lines):
    natoms = int(xyz_lines[0])
    coord_lines = xyz_lines[2 : natoms + 2]
    geom_string = ""
    for coord_line in coord_lines:
        for coord_str in check_str_byte(coord_line).split()[
            :4
        ]:  # QM9 also contains partial charges.
            geom_string += " " + coord_str
        geom_string += "\n"
    return geom_string


def check_str_byte(str_in):
    if isinstance(str_in, str):
        return str_in
    else:
        return str_in.decode("utf-8")


def xyzfile2geom(xyz_file):
    with open(xyz_file, "r") as f:
        return xyzlines2geom(f.readlines())


def str_no_special_chars(input_obj):
    output = input_obj
    for bad_char in ["(", ")", ".", " "]:
        output = output.replace(bad_char, "_")
    return output


def tar_readlines(tar_file, filename):
    return tar_file.extractfile(filename).readlines()


def dump2pkl(obj, filename):
    output_file = open(filename, "wb")
    pickle.dump(obj, output_file)
    output_file.close()


def loadpkl(filename):
    input_file = open(filename, "rb")
    obj = pickle.load(input_file)
    input_file.close()
    return obj


def check_full_path(path_to_entry):
    if path_to_entry[0] == "/":
        return path_to_entry
    else:
        return os.getcwd() + "/" + path_to_entry


def check_create_randomized_list(list_input, randomized_list_dump=None):
    randomized_list_input = None
    if randomized_list_dump is not None:
        if os.path.isfile(randomized_list_dump):
            randomized_list_input = loadpkl(randomized_list_dump)
    if randomized_list_input is None:
        import copy
        import random

        randomized_list_input = copy.deepcopy(list_input)
        random.shuffle(randomized_list_input)
        if randomized_list_dump is not None:
            dump2pkl(randomized_list_input, randomized_list_dump)
    return randomized_list_input
